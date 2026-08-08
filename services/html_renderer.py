class HTMLRenderer:
    """Service to handle all HTML string generation for UI displays."""

    @staticmethod
    def _clean_str(obj) -> str:
        return str(obj).replace("'", "")

    @staticmethod
    def render_lattice(l, colors: dict) -> str:
        c_head, c_acc, c_sub = colors["header"], colors["accent"], colors["subtle"]
        html = f"<h3 style='color:{c_head};'>LATTICE: {l.name}</h3>"
        html += f"<b>Elements ({len(l.elements)}):</b><br>"
        clean_elems = [HTMLRenderer._clean_str(e) for e in sorted(list(l.elements))]
        html += f"<span style='font-family:monospace; color:{c_acc};'>{{{', '.join(clean_elems)}}}</span><br><br>"
        
        html += "<b>Relations (≤):</b><br>"
        rels_fmt = [f"({HTMLRenderer._clean_str(a)},{HTMLRenderer._clean_str(b)})" for a, b in sorted(list(l.relations))]
        html += f"<span style='font-family:monospace; color:{c_sub};'>{', '.join(rels_fmt)}</span><br><br>"
        
        html += "<b>Implication (→):</b><br>"
        if hasattr(l, 'implication_map') and l.implication_map:
            html += "<table border='0' cellspacing='2' cellpadding='2' style='font-family:monospace;'>"
            for (a, b), res in sorted(l.implication_map.items(), key=lambda x: str(x[0])):
                html += f"<tr><td>{HTMLRenderer._clean_str(a)} → {HTMLRenderer._clean_str(b)}</td><td>= <b>{HTMLRenderer._clean_str(res)}</b></td></tr>"
            html += "</table>"
        else:
            html += f"<i style='color:{c_sub};'>(Not defined)</i>"
        return html

    @staticmethod
    def render_twist_structure(ts, colors: dict) -> str:
        c_warn, c_acc, c_sub = colors["warn"], colors["accent"], colors["subtle"]
        html = f"<h3 style='color:{c_warn};'>TWIST STRUCTURE: {ts.name}</h3>"
        html += f"<b>Base RL:</b> {ts.lattice.name}<br><br>"
        html += f"<b>Elements (L x L) [{len(ts.elements)}]:</b><br>"
        sorted_elems = sorted(list(ts.elements), key=lambda x: (str(x[0]), str(x[1])))
        clean_elems_str = [HTMLRenderer._clean_str(e) for e in sorted_elems]
        html += f"<span style='font-family:monospace; color:{c_acc};'>{', '.join(clean_elems_str)}</span><br><br>"
        html += "<b>Truth Ordering (≤<sub>t</sub>):</b><br>"
        sorted_truth = sorted(list(ts.truth_relation), key=lambda x: (str(x[0]), str(x[1])))
        count = 0
        html += "<div style='font-family:monospace; font-size:11px;'>"
        for a, b in sorted_truth:
            if a != b: 
                html += f"{HTMLRenderer._clean_str(a)} ≤<sub>t</sub> {HTMLRenderer._clean_str(b)}<br>"
                count += 1
        if count == 0: html += f"<i style='color:{c_sub};'>(Reflexive only)</i>"
        html += "</div><br>"
        return html

    @staticmethod
    def render_world(w, colors: dict, is_dark: bool) -> str:
        c_info, c_sub = colors["info"], colors["subtle"]
        html = f"<h3 style='color:{c_info};'>STATE: {w.name_long}</h3>"
        html += f"<b>Short Name:</b> {w.name_short}<br>"
        if hasattr(w, 'twist_structure') and w.twist_structure:
            html += f"<b>Twist Structure:</b> {w.twist_structure.name}<br><br>"
        html += "<b>Valuations (V):</b><br>"
        if w.assignments:
            border_c = "#555" if is_dark else "#ddd"
            bg_c = "#333" if is_dark else "#f2f2f2"
            html += f"<table border='1' cellspacing='0' cellpadding='4' style='border-collapse:collapse; border-color:{border_c}; font-family:monospace;'>"
            html += f"<tr style='background-color:{bg_c};'><th>Prop</th><th>Value</th></tr>"
            for p, v in sorted(w.assignments.items()):
                html += f"<tr><td>{p}</td><td style='color:{c_info};'>{HTMLRenderer._clean_str(v)}</td></tr>"
            html += "</table>"
        else:
            html += f"<i style='color:{c_sub};'>(No assignments)</i>"
        return html

    @staticmethod
    def render_model(m, colors: dict) -> str:
        c_err, c_text, c_sub = colors["error"], colors["text"], colors["subtle"]
        html = f"<h3 style='color:{c_err};'>PLTS: {m.name_model}</h3>"
        if hasattr(m, 'description') and m.description:
            html += f"<b>Description:</b><br><i style='color:{c_text};'>{m.description}</i><br><br>"
        html += f"<b>States:</b> {', '.join(sorted([w.name_short for w in m.worlds]))}<br>"
        html += f"<b>Actions:</b> {', '.join(sorted(list(m.actions)))}<br><br>"
        html += "<b>Accessibility Relations (R):</b><br>"
        if not m.actions:
            html += f"<i style='color:{c_sub};'>(No actions defined)</i>"
        else:
            for action in sorted(list(m.actions)):
                html += f"<div style='margin-top:5px; font-weight:bold; color:{c_text};'>[{action}] Transitions:</div>"
                rel_map = m.accessibility_relations.get(action, {})
                sorted_src = sorted(rel_map.keys(), key=lambda w: w.name_short)
                for src in sorted_src:
                    targets = rel_map[src]
                    if targets:
                        valid_targets = {t: w for t, w in targets.items() if w is not None}
                        if valid_targets:
                            edge_strs = [f"{t.name_short} <span style='color:{c_sub}; font-size:10px;'>{HTMLRenderer._clean_str(w)}</span>" 
                                         for t, w in valid_targets.items()]
                            html += f"<div style='margin-left:15px; font-family:monospace; color:{c_text};'>{src.name_short} &#8594; {{ {', '.join(sorted(edge_strs))} }}</div>"
        return html

    @staticmethod
    def render_filtered_model(fm, colors: dict) -> str:
        c_acc, c_text, c_sub = colors["accent"], colors["text"], colors["subtle"]
        html = f"<h3 style='color:{c_acc};'>FILTERED MODEL: {fm.name_model}</h3>"
        if hasattr(fm, 'description') and fm.description:
            html += f"<b>Description:</b><br><i style='color:{c_text};'>{fm.description}</i><br><br>"
        
        base_name = fm.base_model.name_model if hasattr(fm, 'base_model') and fm.base_model else "Unknown"
        filter_name = fm.twist_filter.name if hasattr(fm, 'twist_filter') and fm.twist_filter else "Unknown"
        
        html += f"<b>Base Model:</b> {base_name}<br>"
        html += f"<b>Twist Filter:</b> {filter_name}<br>"
        html += f"<b>States:</b> {', '.join(sorted([w.name_short for w in fm.worlds]))}<br>"
        html += f"<b>Actions:</b> {', '.join(sorted(list(fm.actions)))}<br><br>"
        
        html += "<b>Filtered Crisp Relations:</b><br>"
        if not fm.actions:
            html += f"<i style='color:{c_sub};'>(No actions defined)</i>"
        else:
            for action in sorted(list(fm.actions)):
                html += f"<div style='margin-top:5px; font-weight:bold; color:{c_text};'>[{action}] Transitions:</div>"
                rel_map = fm.accessibility_relations.get(action, {})
                sorted_src = sorted(rel_map.keys(), key=lambda w: w.name_short)
                for src in sorted_src:
                    targets = rel_map[src]
                    if targets:
                        valid_targets = [t.name_short for t in targets.keys() if t is not None]
                        if valid_targets:
                            html += f"<div style='margin-left:15px; font-family:monospace; color:{c_text};'>{src.name_short} &#8594; {{ {', '.join(sorted(valid_targets))} }}</div>"
        return html

    @staticmethod
    def render_symbol_legend(is_dark: bool, info_color: str) -> str:
        text_col, bg_col = ("white", "#333") if is_dark else ("black", "#f0f0f0")
        return f"""
        <h3 style='color:{info_color};'>Symbol Legend</h3>
        <table border="1" cellpadding="4" cellspacing="0" style='border-collapse: collapse; color:{text_col};'>
            <tr style='background-color:{bg_col};'><td><b>Button</b></td><td><b>Input</b></td><td><b>Description</b></td><td><b>Definition</b></td></tr>
            <tr><td>□</td><td>[a]</td><td>Box</td><td>¬&lt;a&gt;¬A</td></tr>
            <tr><td>◇</td><td>&lt;a&gt;</td><td>Diamond</td><td>&lt;a&gt;A</td></tr>
            <tr><td>¬</td><td>~</td><td>Negation</td><td>¬A</td></tr>
            <tr><td>▷</td><td>-&gt;</td><td>Material Imp.</td><td>¬A ⊔ B</td></tr>
            <tr><td>▷◁</td><td>&lt;-&gt;</td><td>Material Iff.</td><td>(A ▷ B) ⊓ (B ▷ A)</td></tr>
            <tr><td>∧</td><td>&</td><td>Weak Meet</td><td>Conjunction (⊓)</td></tr>
            <tr><td>∨</td><td>|</td><td>Weak Join</td><td>Disjunction (⊔)</td></tr>
            <tr><td>⊥</td><td>0 / BOT</td><td>Bottom</td><td>Absolute False</td></tr>
            <tr><td>⊤</td><td>1 / TOP</td><td>Top</td><td>Absolute True</td></tr>
        </table>"""

    @staticmethod
    def render_definitions(colors: dict) -> str:
        c_head, c_text = colors["header"], colors["text"]
        return f"""
        <div style='color:{c_text};'>
        <h3 style='color:{c_head};'>Paraconsistent Definitions</h3>
        <p>Truth values are pairs (t, f) - evidence for/against.</p>
        <h4 style='color:{c_head};'>Logic Operations</h4>
        <ul><li>Negation (¬): ¬(t, f) = (f, t)</li>
            <li>Weak Meet (⊓): (t1, f1) ⊓ (t2, f2) = (t1 ∧ t2, f1 ∨ f2)</li>
            <li>Weak Join (⊔): (t1, f1) ⊔ (t2, f2) = (t1 ∨ t2, f1 ∧ f2)</li>
        </ul>
        <h4 style='color:{c_head};'>Modalities</h4>
        <ul><li>Diamond (⟨a⟩φ): ⊔<sub>v∈W</sub> ( R<sub>a</sub>(w,v) ⊙ V(v, φ) )</li>
            <li>Box ([a]φ): ¬⟨a⟩¬φ</li></ul>
        
        <h4 style='color:{c_head};'>Filters</h4>
        <ul>
            <li>Prime Filter (F): A nonempty subset F &sub; L, satisfying:
                <ul>
                    <li>a ∧ b ∈ F ⟺ (a ∈ F and b ∈ F)</li>
                    <li>a ∨ b ∈ F ⟺ (a ∈ F or b ∈ F)</li>
                </ul>
            </li>
        </ul>
        </div>"""

    @staticmethod
    def render_lattice_filter(lattice_filter, colors: dict) -> str:
        if not lattice_filter:
            return "<p>No Lattice Filter selected.</p>"
        
        elements_str = ", ".join(sorted([HTMLRenderer._clean_str(e) for e in lattice_filter.filter_elements], key=str))
        
        return f"""
        <h3 style="color: {colors.get('header', '#000')};">Lattice Filter: {lattice_filter.name}</h3>
        <p><b>Base Lattice:</b> {lattice_filter.lattice_name}</p>
        <p><b>Filter Elements:</b> {{{elements_str}}}</p>
        """

    @staticmethod
    def render_twist_filter(twist_filter, colors: dict) -> str:
        if not twist_filter:
            return "<p>No Twist Filter selected.</p>"
        
        elements_str = ", ".join(sorted([HTMLRenderer._clean_str(e) for e in twist_filter.filter_elements], key=str))
        
        return f"""
        <h3 style="color: {colors.get('header', '#000')};">Twist Filter: {twist_filter.name}</h3>
        <p><b>Twist Structure:</b> {twist_filter.twist_name}</p>
        <p><b>Underlying Lattice Filter:</b> {twist_filter.lattice_filter.name}</p>
        <p><b>Filter Elements:</b> {{{elements_str}}}</p>
        """

    @staticmethod
    def render_morphism(morphism, colors: dict) -> str:
        if not morphism:
            return "<p>No Morphism selected.</p>"
            
        c_head, c_text, c_sub = colors["header"], colors["text"], colors["subtle"]
        
        html = f"<h3 style='color:{c_head};'>MORPHISM: {morphism.name}</h3>"
        if hasattr(morphism, 'description') and morphism.description:
            html += f"<b>Description:</b><br><i style='color:{c_text};'>{morphism.description}</i><br><br>"
            
        src_name = morphism.source_model.name_model if morphism.source_model else "Unknown"
        tgt_name = morphism.target_model.name_model if morphism.target_model else "Unknown"
        
        html += f"<b>Source PLTS:</b> {src_name}<br>"
        html += f"<b>Target PLTS:</b> {tgt_name}<br><br>"
        
        html += "<b>State Mapping Function (h):</b><br>"
        if morphism.mapping:
            html += "<table border='0' cellspacing='2' cellpadding='2' style='font-family:monospace;'>"
            for src_w, tgt_w in sorted(morphism.mapping.items(), key=lambda x: x[0].name_long):
                src_str = f"{src_w.name_long} ({src_w.name_short})"
                tgt_str = f"{tgt_w.name_long} ({tgt_w.name_short})" if tgt_w else "None"
                html += f"<tr><td>{src_str}</td><td>&#8594;</td><td style='color:{c_head};'><b>{tgt_str}</b></td></tr>"
            html += "</table>"
        else:
            html += f"<i style='color:{c_sub};'>(No mappings defined)</i>"
            
        return html