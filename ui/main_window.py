"""
Main Application Module.

This module defines the MainWindow class, which serves as the primary user interface
for the PLTS Editor.
"""

import sys
from typing import Dict, Set, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QMenu, QMessageBox, QInputDialog, QLabel, QSplitter, QLineEdit, QComboBox, 
    QTreeWidget, QTreeWidgetItem, QFrame, QPushButton, QListWidget, 
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction

from math_objects import Lattice, TwistStructure, World, Model, LatticeFilter, TwistFilter, FilteredModel, PLTSMorphism
from services import ObjectManager, ThemeService, JSONHandler
from parser.formula_parser import FormulaParser 

from app_object_creation import (
    NewLatticeDialog, NewModelDialog,
    NewTwistStructureDialog, NewWorldDialog, NewLatticeFilterDialog, NewFilteredModelDialog, NewMorphismDialog, NewTwistFilterDialog
)
from app_object_loading import MultiSelectDialog
from config import PATHS

from .sidebar import SidebarWidget
from .workspace import WorkspaceWidget
from .interpreter import InterpreterWidget
from services.html_renderer import HTMLRenderer
from services.evaluation_service import EvaluationService
from utils.decorators import handle_ui_errors
from ui.error_dialogs import ErrorHandler
from pathlib import Path
from ui.view_logs_dialog import ViewLogsDialog
from services.logging_service import get_logger



class MainWindow(QMainWindow):
    """
    The main application window containing the workspace, sidebar, and tools.
    """

    def __init__(self, manager: ObjectManager, theme_service: ThemeService):
        """Initializes the main window and internal storage structures."""
        super().__init__()
        self.setWindowTitle("PLTS Toolkit")
        self.resize(1100, 750)
        
        self.manager = manager
        self.theme_service = theme_service
        self.config_file = PATHS["config"]

        self.props: Set[str] = {"p", "q", "r", "s"}

        self.setup_ui()
        self.create_menu()
        
        self.load_user_config()
        self.apply_theme()


    def load_user_config(self) -> None:
        try:
            config = JSONHandler.load_config(self.config_file)
            self.theme_service.is_dark_mode = config.get("dark_mode", False)
        except Exception as e:
            ErrorHandler.show_warning("Config Warning", "Could not load user preferences. Using defaults.", self)
            self.theme_service.is_dark_mode = False

    def save_user_config(self) -> None:
        try:
            config = {"dark_mode": self.theme_service.is_dark_mode}
            JSONHandler.save_config(self.config_file, config)
        except Exception as e:
            ErrorHandler.show_error("Save Error", f"Could not save user preferences: {str(e)}", self)

    def apply_theme(self) -> None:
        try:
            app = QApplication.instance()
            app.setStyle("Fusion")
            
            app.setStyleSheet(self.theme_service.get_stylesheet())
            
            legend_btn = self.interpreter.btn_legend 
            color = self.get_theme_color("accent")
            legend_btn.setStyleSheet(f"font-weight: bold; color: {color};")
            
            if hasattr(self, 'action_dark_mode'):
                self.action_dark_mode.setText("Toggle Light Mode" if self.theme_service.is_dark_mode else "Toggle Dark Mode")
        except Exception as e:
            from services.logging_service import get_logger
            get_logger("MainWindow").error(f"Theme application failed: {str(e)}")

    def get_theme_color(self, role: str) -> str:
        return self.theme_service.get_color(role)

    def toggle_dark_mode(self) -> None:
        try:
            self.theme_service.toggle()
            self.apply_theme()
            self.save_user_config()
        except Exception as e:
            ErrorHandler.show_error("Theme Error", f"Could not toggle theme: {str(e)}", self)


    def setup_ui(self) -> None:
        """Main entry for UI assembly."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        self._setup_sidebar()
        self._setup_workspace_and_interpreter()
        
        self.splitter.setSizes([300, 700])
        self.refresh_props_ui()

    def _setup_sidebar(self):
        """Assembles the sidebar widget and connects its signals."""
        self.sidebar = SidebarWidget()
        self.sidebar.layout().setContentsMargins(5, 5, 5, 5)
        self.sidebar.init_tree_categories(["Lattices", "Lattice Filters", "Twist Structures", "Twist Filters", "States", "PLTSs", "Filtered Models", "Morphisms"])
        
        self.sidebar.add_prop_requested.connect(self.add_proposition)
        self.sidebar.remove_prop_requested.connect(self.remove_proposition)
        self.sidebar.item_clicked.connect(self.on_tree_item_clicked)
        self.sidebar.context_menu_requested.connect(self.open_tree_context_menu)
        
        self.splitter.addWidget(self.sidebar)

    def _setup_workspace_and_interpreter(self):
        """Assembles the workspace and interpreter into the right-hand panel."""
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)
        
        self.workspace = WorkspaceWidget()
        self.workspace.hasse_requested.connect(self.show_current_hasse)
        self.workspace.plts_requested.connect(self.visualize_current_model)
        self.workspace.filtered_plts_requested.connect(self.visualize_current_filtered_model)
        self.workspace.morphism_requested.connect(self.visualize_current_morphism)
        
        self.interpreter = InterpreterWidget()
        self.interpreter.evaluate_requested.connect(self.evaluate_formula)
        self.interpreter.validity_requested.connect(self.check_model_validity)
        self.interpreter.symbol_inserted.connect(self.insert_symbol)
        self.interpreter.btn_legend.clicked.connect(self.show_symbol_legend)
        self.interpreter.combo_models.currentIndexChanged.connect(self.update_world_combo)
        self.interpreter.combo_models.currentIndexChanged.connect(self.update_filter_combo)
        
        right_layout.addWidget(self.workspace)
        right_layout.addWidget(self.interpreter)
        right_layout.addStretch(1)
        
        self.splitter.addWidget(right_container)
    
    def insert_symbol(self, text: str) -> None:
        """Helper to insert symbol from button click into input field."""
        self.interpreter.formula_input.insert(text)
        self.interpreter.formula_input.setFocus()

    def show_symbol_legend(self) -> None:
        html = HTMLRenderer.render_symbol_legend(
            is_dark=self.theme_service.is_dark_mode,
            info_color=self.get_theme_color('info')
        )
        ErrorHandler.show_info("Symbol Legend", html, self)

    def show_definitions(self) -> None:
        colors = {
            "header": self.get_theme_color("header"),
            "text": self.get_theme_color("text")
        }
        html = HTMLRenderer.render_definitions(colors)
        ErrorHandler.show_info("Definitions", html, self)

    def create_menu(self) -> None:
        """Initializes the application menu bar using a data-driven approach."""
        menu_bar = self.menuBar()

        menus = [
            ("New", [
                ("Lattice", self.create_new_lattice),
                ("Lattice Filter", self.create_new_lattice_filter),
                ("Twist Structure", self.create_new_twist_structure),
                ("Twist Filter", self.create_new_twist_filter),
                ("State", self.create_new_world),
                ("PLTS", self.create_new_model),
                ("Filtered Model", self.create_new_filtered_model),
                ("Morphism", self.create_new_morphism)
            ]),
            ("Load", [
                ("Lattice", lambda: self.load_specific_object("Lattice", "lattices", "name")),
                ("Lattice Filter", lambda: self.load_specific_object("Lattice Filter", "lattice_filters", "name")),
                ("Twist Structure", lambda: self.load_specific_object("Twist Structure", "twist_structures", "name")),
                ("Twist Filter", lambda: self.load_specific_object("Twist Filter", "twist_filters", "name")),
                ("State", lambda: self.load_specific_object("World", "worlds", "world_name")),
                ("PLTS", lambda: self.load_specific_object("Model", "models", "model_name")),
                ("Filtered Model", lambda: self.load_specific_object("Filtered Model", "filtered_models", "filtered_model_name")),
                ("Morphism", lambda: self.load_specific_object("Morphism", "morphisms", "name"))
            ]),
            ("Delete", [
                ("Lattice", lambda: self.delete_specific_object("Lattice", "lattices", "name")),
                ("Lattice Filter", lambda: self.delete_specific_object("Lattice Filter", "lattice_filters", "name")),
                ("Twist Structure", lambda: self.delete_specific_object("Twist Structure", "twist_structures", "name")),
                ("Twist Filter", lambda: self.delete_specific_object("Twist Filter", "twist_filters", "name")),
                ("State", lambda: self.delete_specific_object("World", "worlds", "world_name")),
                ("PLTS", lambda: self.delete_specific_object("Model", "models", "model_name")),
                ("Filtered Model", lambda: self.delete_specific_object("Filtered Model", "filtered_models", "filtered_model_name")),
                ("Morphism", lambda: self.delete_specific_object("Morphism", "morphisms", "name"))
            ]),
            ("See", [
                ("Lattices in File", lambda: self.see_objects_in_file("lattices", "name")),
                ("Lattice Filters in File", lambda: self.see_objects_in_file("lattice_filters", "name")),
                ("Twist Structures in File", lambda: self.see_objects_in_file("twist_structures", "name")),
                ("Twist Filters in File", lambda: self.see_objects_in_file("twist_filters", "name")),
                ("States in File", lambda: self.see_objects_in_file("worlds", "world_name")),
                ("PLTSs in File", lambda: self.see_objects_in_file("models", "model_name")),
                ("Filtered Models in File", lambda: self.see_objects_in_file("filtered_models", "filtered_model_name")),
                ("Morphisms in File", lambda: self.see_objects_in_file("morphisms", "name"))
            ])
        ]

        for menu_name, actions in menus:
            menu = menu_bar.addMenu(menu_name)
            for action_name, trigger in actions:
                menu.addAction(action_name).triggered.connect(trigger)

        view_menu = menu_bar.addMenu("View")
        self.action_dark_mode = QAction("Toggle Dark Mode", self)
        self.action_dark_mode.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.action_dark_mode)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("Mathematical Definitions").triggered.connect(self.show_definitions)
        help_menu.addAction("Symbol Legend").triggered.connect(self.show_symbol_legend)
        help_menu.addAction("View Logs").triggered.connect(self.open_view_logs_dialog)


    def refresh_model_combo(self) -> None:
        try:
            self.interpreter.set_model_list(list(self.manager.models.keys()))
            self.update_world_combo()
            self.update_filter_combo()
        except Exception as e:
            ErrorHandler.show_error("UI Update Error", f"Failed to refresh model list: {str(e)}", self)

    def update_world_combo(self) -> None:
        try:
            model_name = self.interpreter.get_selected_model()
            if model_name in self.manager.models:
                model = self.manager.models[model_name]
                world_names = sorted([w.name_long for w in model.worlds])
                self.interpreter.set_world_list(world_names)
        except Exception as e:
            ErrorHandler.show_error("UI Update Error", f"Failed to refresh states list: {str(e)}", self)

    def update_filter_combo(self) -> None:
        try:
            model_name = self.interpreter.get_selected_model()
            filter_names = set()
            
            if model_name in self.manager.models:
                model = self.manager.models[model_name]
                ts_name = model.twist_structure.name if model.twist_structure else None
                
                if ts_name:
                    all_tf_names = JSONHandler.get_names_from_json(PATHS["twist_filters"], "twist_filters", "name")
                    for tf_name in all_tf_names:
                        tf_obj = JSONHandler.load_twist_filter_from_json(PATHS["twist_filters"], tf_name)
                        if tf_obj and tf_obj.twist_name == ts_name:
                            filter_names.add(tf_name)
                            
            self.interpreter.set_filter_list(sorted(list(filter_names)))
        except Exception as e:
            ErrorHandler.show_error("UI Update Error", f"Failed to refresh twist filters list: {str(e)}", self)

    def refresh_props_ui(self) -> None:
        try:
            self.sidebar.refresh_props_ui(self.props)
        except Exception as e:
            ErrorHandler.show_warning("UI Refresh Error", "Failed to refresh propositions list.", self)

    def add_proposition(self) -> None:
        text, ok = QInputDialog.getText(self, "Add Propositions", "Enter propositions, e.g: p, q, r:")
        if ok and text:
            try:
                for item in text.split(','):
                    p = item.strip()
                    if p: 
                        self.props.add(p)
                self.refresh_props_ui()
            except Exception as e:
                ErrorHandler.show_error("Input Error", f"Failed to add propositions: {str(e)}", self)

    def remove_proposition(self) -> None:
        try:
            for item in self.sidebar.prop_list.selectedItems():
                if item.text() in self.props: 
                    self.props.remove(item.text())
            self.refresh_props_ui()
        except Exception as e:
            ErrorHandler.show_error("Input Error", f"Failed to remove propositions: {str(e)}", self)
    
    def open_view_logs_dialog(self) -> None:
        """Opens the dialog to view application logs."""
        try:
            log_path = Path("logs/app.log")
            dialog = ViewLogsDialog(log_path, parent=self)
            dialog.exec()
        except Exception as e:
            get_logger("MainWindow").error(f"Failed to open log dialog: {str(e)}")
            ErrorHandler.show_error("UI Error", "Could not open log viewer.", self)


    def is_object_loaded(self, category: str, name: str) -> bool:
        return self.manager.is_object_loaded(category, name)

    def register_object(self, name: str, obj: Any, type_str: str) -> None:
        self.manager.register_object(name, obj, type_str)
        
        cat_map = {"Lattice": "Lattices", "Lattice Filter": "Lattice Filters","Twist Structure": "Twist Structures", "Twist Filter": "Twist Filters","World": "States", "Model": "PLTSs", "Filtered Model": "Filtered Models", "Morphism": "Morphisms"}
        cat = cat_map.get(type_str)
        
        if hasattr(self.sidebar, 'tree_categories') and cat in self.sidebar.tree_categories:
            parent = self.sidebar.tree_categories[cat]
            for i in range(parent.childCount()):
                if parent.child(i).text(0) == name:
                    return
            
            item = QTreeWidgetItem(parent)
            item.setText(0, name)
            
        if type_str == "Model": self.refresh_model_combo()
        if type_str == "Twist Filter": self.update_filter_combo()

    def remove_from_tree(self, category_label: str, object_name: str) -> None:
        root_item = self.sidebar.tree_categories.get(category_label)
        if not root_item: return
        for i in range(root_item.childCount()):
            child = root_item.child(i)
            if child.text(0) == object_name:
                root_item.removeChild(child)
                break

    def remove_object_from_memory(self, ui_category: str, tree_category_label: str, object_name: str) -> None:
        self.manager.delete_object(ui_category, object_name)
        
        self.remove_from_tree(tree_category_label, object_name)
        self.workspace.details_text.clear()
        self.statusBar().showMessage(f"Removed '{object_name}' from workspace.", 2000)
        
        if ui_category == "Model": 
            self.refresh_model_combo()
        if ui_category == "Twist Filter":
            self.update_filter_combo()


    def see_objects_in_file(self, json_key: str, name_key: str) -> None:
        filename_map = {
            "lattices": PATHS["lattices"],
            "lattice_filters": PATHS["lattice_filters"],
            "twist_structures": PATHS["twist_structures"],
            "twist_filters": PATHS["twist_filters"],
            "worlds": PATHS["worlds"],
            "models": PATHS["models"],
            "filtered_models": PATHS["filtered_models"],
            "morphisms": PATHS["morphisms"]
        }
        fname = filename_map.get(json_key)
        if not fname:
            ErrorHandler.show_error("File Error", f"Invalid storage category key: '{json_key}'", self)
            return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        display_text = "\n".join(names) if names else "No items found."
        ErrorHandler.show_info(f"File Content: {fname}", display_text, self)
    

    def _recursive_register(self, obj: Any) -> None:
        """
        Recursively registers dependencies of an object to ensure they appear in the UI.
        """
        if isinstance(obj, Model):
            self._recursive_register(obj.twist_structure)
            for w in obj.worlds:
                self._recursive_register(w.twist_structure)
                if not self.is_object_loaded("World", w.name_long):
                    self.register_object(w.name_long, w, "World")
        
        elif isinstance(obj, TwistStructure):
            if not self.is_object_loaded("Twist Structure", obj.name):
                self.register_object(obj.name, obj, "Twist Structure")
            
            base_lat = obj.lattice
            base_name = base_lat.name if base_lat else None
            
            if base_name and not self.is_object_loaded("Lattice", base_name):
                if base_lat:
                    self.register_object(base_name, base_lat, "Lattice")
        
        elif isinstance(obj, World):
             self._recursive_register(obj.twist_structure)

        elif isinstance(obj, LatticeFilter):
            if not self.is_object_loaded("Lattice Filter", obj.name):
                self.register_object(obj.name, obj, "Lattice Filter")
            if obj.lattice and not self.is_object_loaded("Lattice", obj.lattice_name):
                self.register_object(obj.lattice_name, obj.lattice, "Lattice")

        elif isinstance(obj, TwistFilter):
            if not self.is_object_loaded("Twist Filter", obj.name):
                self.register_object(obj.name, obj, "Twist Filter")
            if obj.lattice_filter and not self.is_object_loaded("Lattice Filter", obj.lattice_filter.name):
                self._recursive_register(obj.lattice_filter)
            if obj.twist_structure and not self.is_object_loaded("Twist Structure", obj.twist_name):
                self._recursive_register(obj.twist_structure)

        elif isinstance(obj, FilteredModel):
            if not self.is_object_loaded("Model", obj.base_model.name_model):
                self.register_object(obj.base_model.name_model, obj.base_model, "Model")
            self._recursive_register(obj.base_model)
            self._recursive_register(obj.twist_filter)

        elif isinstance(obj, PLTSMorphism):
            if obj.source_model:
                if not self.is_object_loaded("Model", obj.source_model.name_model):
                    self.register_object(obj.source_model.name_model, obj.source_model, "Model")
                self._recursive_register(obj.source_model)
            if obj.target_model:
                if not self.is_object_loaded("Model", obj.target_model.name_model):
                    self.register_object(obj.target_model.name_model, obj.target_model, "Model")
                self._recursive_register(obj.target_model)

    def load_specific_object(self, ui_category: str, json_key: str, name_key: str) -> None:
        filename_map = {
            "Lattice": PATHS["lattices"],
            "Lattice Filter": PATHS["lattice_filters"],
            "Twist Structure": PATHS["twist_structures"],
            "Twist Filter": PATHS["twist_filters"],
            "World": PATHS["worlds"],
            "Model": PATHS["models"],
            "Filtered Model": PATHS["filtered_models"],
            "Morphism": PATHS["morphisms"]
        }
        
        fname = filename_map.get(ui_category)
        
        if not fname: 
            ErrorHandler.show_error("Load Error", f"Unknown category: {ui_category}", self)
            return
        
        name_map = {"Model": "PLTS", "World": "State", "Filtered Model": "Filtered Model"}
        display_name = name_map.get(ui_category, ui_category)

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        if not names:
            ErrorHandler.show_info(f"Load {display_name}", f"No objects found in {fname}.", self)
            return

        dialog = MultiSelectDialog(f"Load {display_name}", names, self)
        if dialog.exec():
            for selected_name in dialog.get_selected_items():
                if self.is_object_loaded(ui_category, selected_name): continue
                
                try:
                    obj = None
                    if ui_category == "Lattice":
                        obj = JSONHandler.load_lattice_from_json(fname, selected_name)
                    elif ui_category == "Lattice Filter":
                        obj = JSONHandler.load_lattice_filter_from_json(fname, selected_name)
                    elif ui_category == "Twist Structure":
                        obj = JSONHandler.load_twist_structure_from_json(fname, selected_name)
                    elif ui_category == "Twist Filter":
                        obj = JSONHandler.load_twist_filter_from_json(fname, selected_name)
                    elif ui_category == "World":
                        obj = JSONHandler.load_world_from_json(fname, selected_name)
                    elif ui_category == "Model":
                        obj = JSONHandler.load_model_from_json(fname, selected_name)
                    elif ui_category == "Filtered Model":
                        obj = JSONHandler.load_filtered_model_from_json(fname, selected_name)
                    elif ui_category == "Morphism":
                        obj = JSONHandler.load_morphism_from_json(fname, selected_name)

                    if obj:
                        self.register_object(selected_name, obj, ui_category)
                        self._recursive_register(obj)
                        
                        self.statusBar().showMessage(f"Loaded {selected_name} and dependencies.", 3000)
                except Exception as e:
                    ErrorHandler.show_error("Load Failed", f"Failed to load {selected_name}: {str(e)}", self)

    def delete_specific_object(self, ui_category: str, json_key: str, name_key: str) -> None:
        filename_map = {
            "Lattice": PATHS["lattices"],
            "Lattice Filter": PATHS["lattice_filters"],
            "Twist Structure": PATHS["twist_structures"],
            "Twist Filter": PATHS["twist_filters"],
            "World": PATHS["worlds"],
            "Model": PATHS["models"],
            "Filtered Model": PATHS["filtered_models"],
            "Morphism": PATHS["morphisms"]
        }
        fname = filename_map.get(ui_category)
        if not fname: return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        name_map = {"Model": "PLTS", "World": "State", "Filtered Model": "Filtered Model"}
        display_name = name_map.get(ui_category, ui_category)
        
        dialog = MultiSelectDialog(f"Delete {display_name}", names, self)
        if dialog.exec():
            to_delete = dialog.get_selected_items()
            if not to_delete: return
            if ErrorHandler.ask_confirmation("Confirm Deletion", f"Delete {len(to_delete)} item(s)?", self):
                handler_map = {
                    "Lattice": JSONHandler.delete_lattice_from_json,
                    "Lattice Filter": JSONHandler.delete_lattice_filter_from_json,
                    "Twist Structure": JSONHandler.delete_twist_structure_from_json,
                    "Twist Filter": JSONHandler.delete_twist_filter_from_json,
                    "World": JSONHandler.delete_world_from_json,
                    "Model": JSONHandler.delete_model_from_json,
                    "Filtered Model": JSONHandler.delete_filtered_model_from_json,
                    "Morphism": JSONHandler.delete_morphism_from_json
                }
                
                cat_map = {
                    "Lattice": "Lattices", 
                    "Lattice Filter": "Lattice Filters",
                    "Twist Structure": "Twist Structures", 
                    "Twist Filter": "Twist Filters",
                    "World": "States", 
                    "Model": "PLTSs",
                    "Filtered Model": "Filtered Models",
                    "Morphism": "Morphisms"
                }
                
                handler = handler_map[ui_category]
                tree_cat = cat_map[ui_category]
                
                for name in to_delete:
                    handler(fname, name)
                    self.remove_object_from_memory(ui_category, tree_cat, name)


    @handle_ui_errors
    def create_new_lattice(self, checked=False) -> None:
        dialog = NewLatticeDialog(self)
        if dialog.exec():
            name, elements, relations, imp_map = dialog.get_data()
            lat = Lattice(name, elements, relations, imp_map)
            if JSONHandler.save_lattice_to_json(PATHS["lattices"], lat):
                try:
                    top_filter_name = f"Top {name}"
                    top_filter_elements = {lat.top}
                    lat_filter = LatticeFilter(top_filter_name, name, top_filter_elements, lat)
                    JSONHandler.save_lattice_filter_to_json(PATHS["lattice_filters"], lat_filter)
                except Exception as e:
                    get_logger("MainWindow").warning(f"Could not auto-generate top filter for lattice '{name}': {str(e)}")

                self.register_object(name, lat, "Lattice")
                self._recursive_register(lat)
                self.statusBar().showMessage(f"Success: Lattice '{name}' and filter '{top_filter_name}' created.", 5000)

    @handle_ui_errors
    def create_new_lattice_filter(self, checked=False) -> None:
        lattice_names = JSONHandler.get_names_from_json(PATHS["lattices"], "lattices", "name")
        if not lattice_names: raise ValueError("No lattices found in file. Create a Lattice first.")
        
        lattices_map = {name: JSONHandler.load_lattice_from_json(PATHS["lattices"], name) for name in lattice_names}
        
        dialog = NewLatticeFilterDialog(lattices_map, self)
        if dialog.exec():
            name, lat_name, elements = dialog.get_data()
            if not name: raise ValueError("Filter name cannot be empty.")
            
            lattice = lattices_map.get(lat_name)
            if lattice.bottom in elements:
                raise ValueError("The bottom element of the lattice cannot be part of a filter.")
                
            lat_filter = LatticeFilter(name, lat_name, elements, lattice)
            if JSONHandler.save_lattice_filter_to_json(PATHS["lattice_filters"], lat_filter):
                twist_names = JSONHandler.get_names_from_json(PATHS["twist_structures"], "twist_structures", "name")
                for ts_name in twist_names:
                    ts_obj = JSONHandler.load_twist_structure_from_json(PATHS["twist_structures"], ts_name)
                    if ts_obj and ts_obj.lattice.name == lat_name:
                        tf_name = f"{name}_twist_{ts_name}"
                        t_filter = TwistFilter(tf_name, ts_name, lat_filter, ts_obj)
                        JSONHandler.save_twist_filter_to_json(PATHS["twist_filters"], t_filter)
                self.register_object(name, lat_filter, "Lattice Filter")
                self._recursive_register(lat_filter)
                self.update_filter_combo()
                self.statusBar().showMessage(f"Success: Lattice Filter '{name}' created with cascading twist filters.", 5000)

    @handle_ui_errors
    def create_new_twist_structure(self, checked=False) -> None:
        lattice_names = JSONHandler.get_names_from_json(PATHS["lattices"], "lattices", "name")
        if not lattice_names: raise ValueError("No lattices found in file. Create a Lattice first.")
        
        lattices_map = {name: JSONHandler.load_lattice_from_json(PATHS["lattices"], name) for name in lattice_names}
        
        dialog = NewTwistStructureDialog(lattices_map, self)
        if dialog.exec():
            name, l_name = dialog.get_data()
            existing_ts = JSONHandler.get_names_from_json(PATHS["twist_structures"], "twist_structures", "name")
            if name in existing_ts: raise ValueError(f"Twist Structure '{name}' exists.")
            
            ts = TwistStructure(lattices_map[l_name])
            ts.name = name
            if JSONHandler.save_twist_structure_to_json(PATHS["twist_structures"], ts, name):
                
                try:
                    lat_filter_names = JSONHandler.get_names_from_json(PATHS["lattice_filters"], "lattice_filters", "name")
                    for lf_name in lat_filter_names:
                        lf_obj = JSONHandler.load_lattice_filter_from_json(PATHS["lattice_filters"], lf_name)
                        if lf_obj and lf_obj.lattice_name == l_name:
                            tf_name = f"{lf_name}_twist_{name}"
                            t_filter = TwistFilter(tf_name, name, lf_obj, ts)
                            JSONHandler.save_twist_filter_to_json(PATHS["twist_filters"], t_filter)
                except Exception as e:
                    get_logger("MainWindow").warning(f"Could not auto-generate twist filters for TS '{name}': {str(e)}")

                self.register_object(name, ts, "Twist Structure")
                self._recursive_register(ts)
                self.statusBar().showMessage(f"Success: TS '{name}' created with cascading twist filters.", 5000)

    @handle_ui_errors
    def create_new_twist_filter(self, checked=False) -> None:
        ts_names = JSONHandler.get_names_from_json(PATHS["twist_structures"], "twist_structures", "name")
        lf_names = JSONHandler.get_names_from_json(PATHS["lattice_filters"], "lattice_filters", "name")
        
        if not ts_names or not lf_names:
            raise ValueError("Twist Structures and Lattice Filters must exist first.")
            
        ts_map = {name: JSONHandler.load_twist_structure_from_json(PATHS["twist_structures"], name) for name in ts_names}
        lf_map = {name: JSONHandler.load_lattice_filter_from_json(PATHS["lattice_filters"], name) for name in lf_names}
        
        dialog = NewTwistFilterDialog(ts_map, lf_map, self)
        if dialog.exec():
            name, ts_name, lf_name = dialog.get_data()
            if not name:
                raise ValueError("Filter name cannot be empty.")
                
            ts_obj = ts_map.get(ts_name)
            lf_obj = lf_map.get(lf_name)
            
            if lf_obj.lattice_name != ts_obj.lattice.name:
                raise ValueError("The underlying Lattice Filter's lattice does not match the Twist Structure's lattice.")
                
            t_filter = TwistFilter(name, ts_name, lf_obj, ts_obj)
            if JSONHandler.save_twist_filter_to_json(PATHS["twist_filters"], t_filter):
                self.register_object(name, t_filter, "Twist Filter")
                self._recursive_register(t_filter)
                self.statusBar().showMessage(f"Success: Twist Filter '{name}' created.", 5000)

    @handle_ui_errors
    def create_new_world(self, checked=False) -> None:
        ts_names = JSONHandler.get_names_from_json(PATHS["twist_structures"], "twist_structures", "name")
        if not ts_names: raise ValueError("No Twist Structures found in file. Create one first.")
        
        ts_map = {name: JSONHandler.load_twist_structure_from_json(PATHS["twist_structures"], name) for name in ts_names}
        existing_worlds = JSONHandler.get_names_from_json(PATHS["worlds"], "worlds", "world_name")
        
        dialog = NewWorldDialog(ts_map, self.props, self)
        if dialog.exec():
            created_count = 0
            for (long_name, short_name, ts_name, assignments) in dialog.get_data():
                if long_name in existing_worlds: raise ValueError(f"'{long_name}' exists.")
                w = World(long_name, short_name, ts_map[ts_name], assignments)
                if JSONHandler.save_world_to_json(PATHS["worlds"], w):
                    self.register_object(long_name, w, "World")
                    self._recursive_register(w)
                    created_count += 1
            self.statusBar().showMessage(f"Successfully created {created_count} states.", 5000)

    @handle_ui_errors
    def create_new_model(self, checked=False) -> None:
        ts_names = JSONHandler.get_names_from_json(PATHS["twist_structures"], "twist_structures", "name")
        world_names = JSONHandler.get_names_from_json(PATHS["worlds"], "worlds", "world_name")
        if not world_names or not ts_names:
            raise ValueError("Create Worlds and Twist Structures in files first.")
            
        ts_map = {name: JSONHandler.load_twist_structure_from_json(PATHS["twist_structures"], name) for name in ts_names}
        world_map = {name: JSONHandler.load_world_from_json(PATHS["worlds"], name) for name in world_names}
        
        dialog = NewModelDialog(ts_map, world_map, self.props, self)
        if dialog.exec():
            name, ts_name, w_names, props, rel_data_dict, description = dialog.get_data()
            ts = ts_map[ts_name]
            final_rels = {act: {world_map[s]: {world_map[t]: w for t, w in targets.items()} 
                         for s, targets in matrix.items()} for act, matrix in rel_data_dict.items()}
            m = Model(name, ts, {world_map[wn] for wn in w_names}, final_rels, props, description=description)
            if JSONHandler.save_model_to_json(PATHS["models"], m):
                self.register_object(name, m, "Model")
                self._recursive_register(m)
                self.statusBar().showMessage(f"Success: Model '{name}' created.", 5000)

    @handle_ui_errors
    def create_new_filtered_model(self, checked=False) -> None:
        model_names = JSONHandler.get_names_from_json(PATHS["models"], "models", "model_name")
        if not model_names:
            raise ValueError("No PLTS models found in file. Create a PLTS model first.")
        
        twist_filter_names = JSONHandler.get_names_from_json(PATHS["twist_filters"], "twist_filters", "name")
        if not twist_filter_names:
            raise ValueError("No twist filters found in file. Create a Twist Filter first.")
        
        twist_filters_map = {name: JSONHandler.load_twist_filter_from_json(PATHS["twist_filters"], name) for name in twist_filter_names}

        dialog = NewFilteredModelDialog(model_names, twist_filters_map, self)
        if dialog.exec():
            base_model_name, filter_name, filtered_model_name = dialog.get_data()
            
            base_model = JSONHandler.load_model_from_json(PATHS["models"], base_model_name)
            twist_filter = twist_filters_map.get(filter_name) or JSONHandler.load_twist_filter_from_json(PATHS["twist_filters"], filter_name)

            if not base_model or not twist_filter:
                raise ValueError("Could not load selected base model or twist filter.")

            filtered_model = FilteredModel(base_model, twist_filter, name_model=filtered_model_name)
            
            if JSONHandler.save_filtered_model_to_json(PATHS["filtered_models"], filtered_model):
                self.register_object(filtered_model_name, filtered_model, "Filtered Model")
                self._recursive_register(filtered_model)
                self.statusBar().showMessage(f"Success: Filtered Model '{filtered_model.name_model}' created.", 5000)

    @handle_ui_errors
    def create_new_morphism(self, checked=False) -> None:
        model_names = JSONHandler.get_names_from_json(PATHS["models"], "models", "model_name")
        if len(model_names) < 2:
            raise ValueError("At least two PLTS models are required in files to create a morphism.")
        
        models_map = {name: JSONHandler.load_model_from_json(PATHS["models"], name) for name in model_names}
        
        dialog = NewMorphismDialog(models_map, self)
        if dialog.exec():
            name, morphism = dialog.get_data()
            if JSONHandler.save_morphism_to_json(PATHS["morphisms"], morphism):
                self.register_object(name, morphism, "Morphism")
                self._recursive_register(morphism)
                self.statusBar().showMessage(f"Success: Morphism '{name}' created and saved.", 5000)


    @handle_ui_errors
    def on_tree_item_clicked(self, item: QTreeWidgetItem) -> None:
        parent = item.parent()
        if not parent:
            return
        cat, name = parent.text(0), item.text(0)

        self.workspace.btn_hasse.setEnabled(cat in ["Lattices", "Twist Structures"])
        self.workspace.btn_plts.setEnabled(cat == "PLTSs")
        self.workspace.btn_filtered_plts.setEnabled(cat == "Filtered Models")
        self.workspace.btn_morphism.setEnabled(cat == "Morphisms")

        colors = {
            "header": self.get_theme_color("header"),
            "accent": self.get_theme_color("accent"),
            "warn": self.get_theme_color("warn"),
            "info": self.get_theme_color("info"),
            "error": self.get_theme_color("error"),
            "text": self.get_theme_color("text"),
            "subtle": self.get_theme_color("subtle")
        }

        try:
            html = ""
            if cat == "Lattices":
                html = HTMLRenderer.render_lattice(self.manager.lattices.get(name), colors)
            elif cat == "Lattice Filters":
                html = HTMLRenderer.render_lattice_filter(self.manager.lattice_filters.get(name), colors)
            elif cat == "Twist Structures":
                html = HTMLRenderer.render_twist_structure(self.manager.twist_structures.get(name), colors)
            elif cat == "Twist Filters":
                html = HTMLRenderer.render_twist_filter(self.manager.twist_filters.get(name), colors)
            elif cat == "States":
                html = HTMLRenderer.render_world(self.manager.worlds.get(name), colors, self.theme_service.is_dark_mode)
            elif cat == "PLTSs":
                html = HTMLRenderer.render_model(self.manager.models.get(name), colors)
            elif cat == "Filtered Models":
                html = HTMLRenderer.render_filtered_model(self.manager.filtered_models.get(name), colors)
            elif cat == "Morphisms":
                html = HTMLRenderer.render_morphism(self.manager.morphisms.get(name), colors)

            self.workspace.details_text.setHtml(html)
        except Exception as e:
            ErrorHandler.show_error("Rendering Error", f"Could not render '{name}': {str(e)}", self)
            raise

    @handle_ui_errors
    def visualize_current_model(self) -> None:
        item = self.sidebar.tree.currentItem()
        if not item or not item.parent() or item.parent().text(0) != "PLTSs":
            raise ValueError("Please select a PLTS in the Project Explorer tree to visualize.")
        self.manager.models[item.text(0)].draw_graph()

    @handle_ui_errors
    def visualize_current_filtered_model(self) -> None:
        item = self.sidebar.tree.currentItem()
        if not item or not item.parent() or item.parent().text(0) != "Filtered Models":
            raise ValueError("Please select a Filtered Model in the Project Explorer tree to visualize.")
        
        filtered_model_obj = self.manager.filtered_models.get(item.text(0))
        if filtered_model_obj:
            filtered_model_obj.draw_graph()

    @handle_ui_errors
    def visualize_current_morphism(self) -> None:
        item = self.sidebar.tree.currentItem()
        if not item or not item.parent() or item.parent().text(0) != "Morphisms":
            raise ValueError("Please select a Morphism in the Project Explorer tree to visualize.")

        morphism_obj = self.manager.morphisms.get(item.text(0))
        if morphism_obj:
            morphism_obj.draw_graph()

    @handle_ui_errors
    def show_current_hasse(self) -> None:
        item = self.sidebar.tree.currentItem()
        if item and item.parent():
            cat, name = item.parent().text(0), item.text(0)
            obj = None
            if cat == "Lattices": obj = self.manager.lattices.get(name)
            elif cat == "Twist Structures": obj = self.manager.twist_structures.get(name)
            if obj: obj.draw_hasse()

    def open_tree_context_menu(self, pos: QPoint) -> None:
        item = self.sidebar.tree.itemAt(pos)
        if item and item.parent():
            name = item.text(0)
            cat = item.parent().text(0)
            menu = QMenu()
            action = menu.addAction(f"Remove {name}")
            
            if menu.exec(self.sidebar.tree.viewport().mapToGlobal(pos)) == action:
                cat_map = {
                    "Lattices": "Lattice",
                    "Lattice Filters": "Lattice Filter",  
                    "Twist Structures": "Twist Structure",
                    "Twist Filters": "Twist Filter", 
                    "States": "World", 
                    "PLTSs": "Model",
                    "Filtered Models": "Filtered Model",
                    "Morphisms": "Morphism"
                }
                
                if cat in cat_map:
                    try:
                        self.remove_object_from_memory(cat_map[cat], cat, name)
                    except Exception as e:
                        ErrorHandler.show_error(
                            "Deletion Failed", 
                            f"Could not remove '{name}': {str(e)}", 
                            self
                        )

    @handle_ui_errors
    def evaluate_formula(self) -> None:
        f_str = self.interpreter.formula_input.text().strip()
        m_name = self.interpreter.get_selected_model()
        w_name = self.interpreter.get_selected_world()
        tf_name = self.interpreter.get_selected_filter()
        if not f_str or not m_name or not w_name:
            raise ValueError("Select PLTS, State, and enter formula.")
        
        target_world = next((w for w in self.manager.models[m_name].worlds if w.name_long == w_name), None)
        if not target_world:
            raise ValueError(f"State '{w_name}' not found in model '{m_name}'.")
        
        res_str = EvaluationService.evaluate(f_str, self.manager.models[m_name], target_world)
        
        filter_status = ""
        if tf_name:
            t_filter = self.manager.twist_filters.get(tf_name) or JSONHandler.load_twist_filter_from_json(PATHS["twist_filters"], tf_name)
            if t_filter:
                try:
                    eval_val = eval(res_str) if isinstance(res_str, str) and res_str.startswith("(") else res_str
                    
                    norm_elements = {tuple(str(x).replace("'", "").strip() for x in e) if isinstance(e, tuple) else str(e).replace("'", "").strip() for e in t_filter.filter_elements}
                    norm_eval = tuple(str(x).replace("'", "").strip() for x in eval_val) if isinstance(eval_val, tuple) else str(eval_val).replace("'", "").strip()
                    
                    in_filter = norm_eval in norm_elements
                    filter_status = f" | [In Filter: <b>{'Yes' if in_filter else 'No'}</b>]"
                except Exception:
                    pass
        self.interpreter.validity_label.clear()
        self.interpreter.result_label.setText(f"Result: <b>{res_str}</b>{filter_status}")
        self.statusBar().showMessage(f"Evaluated: {res_str}", 5000)

    @handle_ui_errors
    def check_model_validity(self) -> None:
        f_str = self.interpreter.formula_input.text().strip()
        m_name = self.interpreter.get_selected_model()
        tf_name = self.interpreter.get_selected_filter()
        if not f_str or not m_name: raise ValueError("Select PLTS and enter formula.")
        
        try:
            t_filter = None
            if tf_name:
                t_filter = self.manager.twist_filters.get(tf_name) or JSONHandler.load_twist_filter_from_json(PATHS["twist_filters"], tf_name)

            results, meet_all = EvaluationService.check_validity(f_str, self.manager.models[m_name], twist_filter=t_filter)
            
            msg_results = "<br>".join([f"{p[0]}: {p[1]}" for p in results])

            self.interpreter.result_label.clear()
            self.interpreter.validity_label.setText(f"<div><b>Global Satisfaction:</b> {meet_all}</div><br>{msg_results}")
            self.statusBar().showMessage(f"Checked {m_name}.", 5000)
        except Exception:
            self.interpreter.validity_label.setText("Global Satisfaction: Error")
            raise