from datetime import date
import copy, io, csv, json
import pandas as pd
import streamlit as st
from relationship_actions import add_relationship, modify_relationship, end_relationship
from core import load, save, validate, flatten, move, next_id, active, write_csv, DATA

st.set_page_config(page_title='Hierarchy Studio', page_icon='🌐', layout='wide',
                   initial_sidebar_state='collapsed')

# ---------------------------------------------------------------- theme ----
NAVY, BLUE, PAGE, CARD = '#170F50', '#1010EB', '#EEF1F8', '#FFFFFF'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
:root {{ color-scheme: light; }}
html, body, [class*="css"], .stApp {{ font-family:'Montserrat',sans-serif; color:{NAVY}; }}
.stApp {{ background:{PAGE}; }}
#MainMenu, footer {{ visibility:hidden; }}
header[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{ display:none; }}
.block-container {{ padding-top:2.2rem; max-width:1400px; }}

/* Keep native inputs and their labels readable in the light theme. */
[data-testid="stAppViewContainer"] {{ color:{NAVY}; }}
[data-testid="stWidgetLabel"] p, .stMarkdown p {{ color:{NAVY}; }}
input, textarea {{ color:{NAVY}; }}

/* Top banner */
.topbar {{ background:{CARD}; border:1px solid #e3e6f2; border-bottom:0;
          border-radius:16px 16px 0 0; padding:20px 30px 14px;
          display:flex; align-items:center; justify-content:space-between; }}
.topbar .brand {{ color:{NAVY}; font-size:1.75rem; font-weight:700; letter-spacing:-.5px; }}
.topbar .brand span {{ color:{BLUE}; }}
.topbar .tag {{ color:{NAVY}; font-size:.85rem; font-weight:500; border:1px solid #d9ddf0;
               border-radius:999px; padding:6px 16px; }}

/* Big top navigation tabs (radio with key="nav") */
.st-key-nav {{ background:{CARD}; border:1px solid #e3e6f2; border-top:0;
              border-radius:0 0 16px 16px; padding:6px 22px 18px; margin-top:-1rem;
              margin-bottom:8px; box-shadow:0 6px 18px #170f5018; }}
.st-key-nav [role="radiogroup"] {{ display:flex; flex-wrap:wrap; gap:10px; }}
.st-key-nav label {{ padding:13px 26px; border-radius:999px; border:1.5px solid #d9ddf0;
                    cursor:pointer; transition:all .15s; margin:0; }}
.st-key-nav label:hover {{ background:#eef1f8; }}
.st-key-nav label:has(input:checked) {{ background:{BLUE}; border-color:{BLUE}; box-shadow:0 4px 12px #1010eb66; }}
.st-key-nav label > div:first-child {{ display:none; }}
.st-key-nav label p {{ color:{NAVY} !important; font-size:1.08rem; font-weight:600; margin:0; }}
.st-key-nav label:has(input:checked) p {{ color:#fff !important; }}

/* Page heading */
.page-head h2 {{ margin:14px 0 0; font-weight:700; color:{NAVY}; }}
.page-head p {{ margin:2px 0 14px; color:#5b5787; font-size:.95rem; }}

/* Buttons: pill shaped like the "Read more" button */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {{
    border-radius:999px; border:1.5px solid {BLUE}; color:{BLUE}; background:#fff;
    font-weight:600; padding:.55rem 1.7rem; transition:all .15s; }}
.stButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {{ background:{BLUE}; color:#fff; border-color:{BLUE}; }}
button[kind="primary"], button[kind="primaryFormSubmit"] {{ background:{BLUE} !important; color:#fff !important; }}

/* Dashboard cards */
[data-testid="stVerticalBlockBorderWrapper"] {{ background:{CARD}; border:1px solid #e3e6f2 !important;
    border-radius:16px; box-shadow:0 2px 12px #170f5012; }}
[data-testid="stMetric"] {{ background:{CARD}; border:1px solid #e3e6f2; border-left:6px solid {BLUE};
    border-radius:14px; padding:16px 20px; box-shadow:0 2px 12px #170f5012; }}
[data-testid="stMetricLabel"] {{ color:#5b5787; font-weight:600; }}
[data-testid="stMetricValue"] {{ color:{NAVY}; font-weight:700; }}
[data-testid="stForm"] {{ background:#F6F8FD; border:1px solid #e3e6f2; border-radius:14px; padding:20px; }}
[data-testid="stDataFrame"] {{ border:1px solid #e3e6f2; border-radius:12px; overflow:hidden; }}
.step {{ background:#F6F8FD; border-radius:14px; padding:16px; height:100%; }}
.step .n {{ display:inline-flex; width:30px; height:30px; border-radius:50%; background:{BLUE};
           color:#fff; font-weight:700; align-items:center; justify-content:center; margin-bottom:8px; }}
.step b {{ display:block; margin-bottom:4px; }}
.step small {{ color:#5b5787; }}
.section-title {{ font-weight:700; font-size:1.05rem; margin:0 0 6px; }}

/* Inner tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
.stTabs [data-baseweb="tab"] {{ border-radius:999px; padding:8px 20px; background:#EEF1F8; font-weight:600; }}
.stTabs [aria-selected="true"] {{ background:{BLUE}; color:#fff; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}
</style>
""", unsafe_allow_html=True)


def page_header(title, subtitle):
    st.markdown(f'<div class="page-head"><h2>{title}</h2><p>{subtitle}</p></div>', unsafe_allow_html=True)


def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


st.markdown(
    '<div class="topbar"><div class="brand">Hierarchy <span>Studio</span></div>'
    '<div class="tag">RST hierarchy management · CSV proof of concept</div></div>',
    unsafe_allow_html=True)

try:
    db = load()
except Exception as e:
    st.error(f'Cannot load CSV files: {e}'); st.stop()

PAGES = {'Overview': '🏠', 'Nodes': '🔹', 'Hierarchies & rules': '📐', 'Relationships': '🔗',
         'Hierarchy explorer': '🌳', 'Validation': '✅', 'Reporting output': '📊'}
page = st.radio('Navigation', list(PAGES), format_func=lambda p: f'{PAGES[p]}  {p}',
                horizontal=True, label_visibility='collapsed', key='nav')

if 'notice' in st.session_state:
    st.success(st.session_state.pop('notice'))


def commit(candidate, table):
    try:
        save(candidate, table)
    except (ValueError, OSError) as e:
        st.error(str(e)); return
    st.session_state['notice'] = 'Saved successfully.'
    st.rerun()


def show(rows):
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def label(n):
    r = next(r for r in db['nodes'] if r['node_id'] == n)
    return f"{r['node_name']} · ID {n}"


def hselect(key):
    return st.selectbox('Hierarchy', [h['hier_id'] for h in db['hierarchies']],
                        format_func=lambda x: next(h['hier_desc'] for h in db['hierarchies'] if h['hier_id'] == x),
                        key=key)


# ------------------------------------------------------------- Overview ----
if page == 'Overview':
    page_header('Dashboard', 'A live snapshot of your hierarchy data.')
    today = date.today().isoformat()
    linked = {r['child'] for r in db['node_relationships']}
    unassigned = [n for n in db['nodes'] if n['node_id'] != '0' and n['node_id'] not in linked]
    errors = validate(db)

    k = st.columns(5)
    k[0].metric('Nodes', len(db['nodes']))
    k[1].metric('Hierarchies', len(db['hierarchies']))
    k[2].metric('Relationships', len(db['node_relationships']))
    k[3].metric('Active today', sum(1 for r in db['node_relationships'] if active(r, today)))
    k[4].metric('Validation', 'Passed' if not errors else f'{len(errors)} issue(s)')

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        section('Nodes by type')
        type_names = {t['node_type_id']: t['node_type_name'] for t in db['node_types']}
        counts = pd.Series([type_names.get(n['node_type_id'], n['node_type_id']) for n in db['nodes']]).value_counts()
        st.bar_chart(counts, color=BLUE, height=260)
    with c2, st.container(border=True):
        section('Relationships by hierarchy')
        hnames = {h['hier_id']: h['hier_desc'] for h in db['hierarchies']}
        rel = pd.Series([hnames.get(r['hier_id'], r['hier_id']) for r in db['node_relationships']]).value_counts()
        if len(rel):
            st.bar_chart(rel, color=BLUE, height=260)
        else:
            st.info('No relationships yet.')

    with st.container(border=True):
        section('Start your demonstration')
        steps = [('Explore', 'Open the Hierarchy explorer and follow the Canada path.'),
                 ('Rename', 'Go to Nodes and rename any node.'),
                 ('Report', 'Generate the report from Reporting output.'),
                 ('Move', 'Add another compatible parent, then move a branch using a later effective date.')]
        for col, (i, (t, d)) in zip(st.columns(4), enumerate(steps, 1)):
            col.markdown(f'<div class="step"><div class="n">{i}</div><b>{t}</b><small>{d}</small></div>',
                         unsafe_allow_html=True)
        st.caption(f'{len(unassigned)} workbook entries are deliberately unassigned until real mappings are supplied.')

    with st.container(border=True):
        section('CSV tables')
        t1, t2 = st.columns([4, 1])
        table = t1.selectbox('Table', list(db))
        show(db[table])
        t2.download_button('⬇ Download table', (DATA / f'{table}.csv').read_bytes(), f'{table}.csv', 'text/csv')
    with st.expander('About this demo'):
        st.caption('Demo mappings only. Master names come from HierDesign.xlsx; sample tower and connections '
                   'are illustrative. Local single-user use. Changes are saved to the data folder and previous '
                   'table versions are kept as .csv.bak files.')

# ---------------------------------------------------------------- Nodes ----
elif page == 'Nodes':
    page_header('Nodes', 'Browse, add and rename the building blocks of your hierarchies.')
    with st.container(border=True):
        typ = st.selectbox('Node type', [t['node_type_id'] for t in db['node_types']],
                           format_func=lambda x: next(t['node_type_name'] for t in db['node_types'] if t['node_type_id'] == x))
        tab_browse, tab_add, tab_rename = st.tabs(['Browse', 'Add node', 'Rename node'])

        with tab_browse:
            show([n for n in db['nodes'] if n['node_type_id'] == typ])

        with tab_add:
            with st.form('add_node'):
                name = st.text_input('New node name')
                if st.form_submit_button('Add node', type='primary'):
                    if typ == '0': st.error('Only the existing root is supported.')
                    elif not name.strip(): st.error('Enter a name.')
                    elif any(n['node_type_id'] == typ and n['node_name'].casefold() == name.strip().casefold()
                             for n in db['nodes']):
                        st.error('This name already exists for the selected type.')
                    else:
                        d = copy.deepcopy(db)
                        d['nodes'].append({'node_id': next_id(d['nodes'], 'node_id'), 'node_type_id': typ,
                                           'node_name': name.strip()})
                        commit(d, 'nodes')

        with tab_rename:
            ids = [n['node_id'] for n in db['nodes'] if n['node_type_id'] == typ and n['node_id'] != '0']
            if ids:
                node = st.selectbox('Node to rename', ids, format_func=label)
                with st.form('rename'):
                    name = st.text_input('Updated name', value=next(n['node_name'] for n in db['nodes'] if n['node_id'] == node))
                    if st.form_submit_button('Save name', type='primary'):
                        if not name.strip(): st.error('Name is required.')
                        elif any(n['node_id'] != node and n['node_type_id'] == typ and
                                 n['node_name'].casefold() == name.strip().casefold() for n in db['nodes']):
                            st.error('Name already exists for this type.')
                        else:
                            d = copy.deepcopy(db)
                            next(n for n in d['nodes'] if n['node_id'] == node)['node_name'] = name.strip()
                            commit(d, 'nodes')
            else:
                st.info('No renameable nodes of this type.')

# ---------------------------------------------------- Hierarchies & rules ----
elif page == 'Hierarchies & rules':
    page_header('Hierarchies & rules', 'Create hierarchies and define the ordered levels they follow.')
    with st.container(border=True):
        tab_list, tab_new, tab_edit, tab_rules = st.tabs(['All hierarchies', 'Create new', 'Edit selected', 'Level rules'])

        with tab_list:
            show(db['hierarchies'])

        with tab_new:
            with st.form('new_h'):
                name = st.text_input('New hierarchy name')
                if st.form_submit_button('Create hierarchy', type='primary'):
                    if name.strip():
                        d = copy.deepcopy(db)
                        d['hierarchies'].append({'hier_id': next_id(d['hierarchies'], 'hier_id'),
                                                 'hier_desc': name.strip(), 'active': 'Y'})
                        commit(d, 'hierarchies')
                    else:
                        st.error('Name is required.')

        with tab_edit:
            hid = hselect('edit_sel')
            selected = next(h for h in db['hierarchies'] if h['hier_id'] == hid)
            with st.form('edit_h'):
                name = st.text_input('Hierarchy description', selected['hier_desc'])
                enabled = st.checkbox('Active', selected['active'] == 'Y')
                if st.form_submit_button('Save hierarchy', type='primary'):
                    d = copy.deepcopy(db)
                    h = next(h for h in d['hierarchies'] if h['hier_id'] == hid)
                    h.update(hier_desc=name.strip(), active='Y' if enabled else 'N')
                    commit(d, 'hierarchies')

        with tab_rules:
            hid = hselect('rules_h')
            show([r for r in db['level_rules'] if r['hier_id'] == hid])
            st.caption('Choose types in order. Rule changes are blocked once this hierarchy has relationships.')
            types = {t['node_type_id']: t['node_type_name'] for t in db['node_types'] if t['node_type_id'] != '0'}
            chain = st.multiselect('Ordered levels', list(types), format_func=types.get,
                                   default=[r['child_node_type'] for r in sorted(db['level_rules'], key=lambda x: int(x['level']))
                                            if r['hier_id'] == hid])
            if st.button('Save level rules', type='primary'):
                if any(r['hier_id'] == hid for r in db['node_relationships']):
                    st.error('Create a new hierarchy to use a different level structure.')
                elif not chain:
                    st.error('Select at least one level.')
                else:
                    d = copy.deepcopy(db)
                    d['level_rules'] = [r for r in d['level_rules'] if r['hier_id'] != hid]
                    for i, t in enumerate(chain):
                        d['level_rules'].append({'hier_id': hid, 'level': str(i + 1),
                                                 'parent_node_type': '0' if i == 0 else chain[i - 1], 'child_node_type': t})
                    commit(d, 'level_rules')

# --------------------------------------------------------- Relationships ----
elif page == 'Relationships':
    page_header('Relationships', 'Connect parents and children, change a parent, or end a link with effective dates.')
    with st.container(border=True):
        hid = hselect('rel_h')
        show([r for r in db['node_relationships'] if r['hier_id'] == hid])
    rules = sorted([r for r in db['level_rules'] if r['hier_id'] == hid], key=lambda r: int(r['level']))
    if not rules:
        st.warning('Define level rules first.'); st.stop()
    with st.container(border=True):
        level = st.selectbox('Level', [r['level'] for r in rules])
        rule = next(r for r in rules if r['level'] == level)
        parents = [n['node_id'] for n in db['nodes'] if n['node_type_id'] == rule['parent_node_type']]
        children = [n['node_id'] for n in db['nodes'] if n['node_type_id'] == rule['child_node_type']]
        if not parents or not children:
            st.warning('Add nodes of the required types first.'); st.stop()
        action = st.radio('Action', ['Add new relationship', 'Modify relationship', 'End relationship'], horizontal=True)
        st.caption('Dates are effective dates. End is exclusive. Closed rows remain in history.')

        if action == 'Add new relationship':
            with st.form('add_relationship'):
                c1, c2, c3 = st.columns(3)
                parent = c1.selectbox('Parent', parents, format_func=label)
                child = c2.selectbox('Child', children, format_func=label)
                start = c3.date_input('Start date', date.today())
                st.caption('A new relationship ID is generated. End date stays blank.')
                if st.form_submit_button('Add relationship', type='primary'):
                    try:
                        d = add_relationship(db, hid, level, parent, child, start.isoformat())
                        commit(d, 'node_relationships')
                    except ValueError as e:
                        st.error(str(e))
        else:
            rr = [r for r in db['node_relationships'] if r['hier_id'] == hid and r['level'] == level and not r['end']]
            if not rr:
                st.info('No open-ended relationships at this level. Closed relationships remain in the history table.')
            else:
                by_id = {r['relationship_id']: r for r in rr}

                def relationship_label(x):
                    r = by_id[x]
                    return f"ID {x}: {label(r['parent'])} → {label(r['child'])} | Start: {r['start']}"

                rid = st.selectbox('Select existing relationship', list(by_id), format_func=relationship_label)
                selected = by_id[rid]
                if action == 'Modify relationship':
                    alternatives = [p for p in parents if p != selected['parent']]
                    st.write('Child:', label(selected['child']))
                    st.caption('Changing parent ends the selected row and creates a new ID for the same child. '
                               'Descendants remain attached.')
                    if not alternatives:
                        st.info('Add another parent node of the required type first.')
                    else:
                        with st.form(f'modify_relationship_{rid}'):
                            c1, c2 = st.columns(2)
                            parent = c1.selectbox('New parent', alternatives, format_func=label)
                            when = c2.date_input('Effective change date', date.today())
                            if st.form_submit_button('Modify relationship', type='primary'):
                                try:
                                    d = modify_relationship(db, rid, parent, when.isoformat())
                                    commit(d, 'node_relationships')
                                except ValueError as e:
                                    st.error(str(e))
                else:
                    with st.form(f'end_relationship_{rid}'):
                        when = st.date_input('End date', date.today())
                        st.caption('Keeps the selected relationship ID. No replacement row is created.')
                        if st.form_submit_button('End relationship', type='primary'):
                            try:
                                d = end_relationship(db, rid, when.isoformat())
                                commit(d, 'node_relationships')
                            except ValueError as e:
                                st.error(str(e))

# ------------------------------------------------------------ Validation ----
elif page == 'Validation':
    page_header('Validation', 'Check the structural health of your data.')
    errors = validate(db)
    with st.container(border=True):
        if errors:
            for e in errors: st.error(e)
        else:
            st.success('Structural validation passed: IDs, references, types, date intervals and overlapping parent assignments.')
    linked = {r['child'] for r in db['node_relationships']}
    with st.container(border=True):
        section('Nodes without any child assignment')
        st.caption('Expected for workbook names whose business mappings have not been supplied.')
        show([n for n in db['nodes'] if n['node_id'] != '0' and n['node_id'] not in linked])

# ------------------------------------------- Explorer / Reporting output ----
else:
    if page == 'Hierarchy explorer':
        page_header('Hierarchy explorer', 'See how nodes connect on any date.')
    else:
        page_header('Reporting output', 'Review, save and download the flattened rst_hier report.')
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            hid = hselect('view_h')
        day = c2.date_input('As of date', date.today()).isoformat()
    try:
        rows, cols, warnings = flatten(db, hid, day)
    except ValueError as e:
        st.error(str(e)); st.stop()
    for w in warnings: st.warning(w)

    if page == 'Hierarchy explorer':
        edges = [r for r in db['node_relationships'] if r['hier_id'] == hid and active(r, day)]
        dot = ['digraph G {', 'bgcolor="transparent";', 'rankdir=TB;',
               f'node [shape=box style="rounded,filled" fillcolor="{CARD}" fontcolor="{NAVY}" '
               f'color="{BLUE}" fontname="Arial" margin="0.2,0.1"];',
               f'edge [color="{BLUE}" penwidth=1.5];']
        ids = {x for r in edges for x in (r['parent'], r['child'])}
        for n in ids: dot.append(f'{json.dumps(n)} [label={json.dumps(label(n))}];')
        for r in edges: dot.append(f'{json.dumps(r["parent"])} -> {json.dumps(r["child"])};')
        dot.append('}')
        with st.container(border=True):
            if edges:
                st.graphviz_chart('\n'.join(dot))
            else:
                st.info('No active relationships for this hierarchy on the selected date.')
    else:
        m1, _ = st.columns([1, 3])
        m1.metric('Rows in report', len(rows))
        with st.container(border=True):
            st.caption('One row per complete path to the final configured level. Incomplete paths are excluded '
                       'and flagged above. Names reflect current node names even for historical dates.')
            st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True, hide_index=True)
            b1, b2, _ = st.columns([1.3, 1.3, 3])
            if b1.button('Generate and save rst_hier.csv', type='primary'):
                write_csv(DATA / 'rst_hier.csv', rows, cols)
                st.success('Snapshot saved. Regenerate after changes.')
            buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols); w.writeheader(); w.writerows(rows)
            b2.download_button('⬇ Download current report', buf.getvalue(), 'rst_hier.csv', 'text/csv')
