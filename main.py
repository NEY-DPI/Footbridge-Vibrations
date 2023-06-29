import streamlit as st
import pandas as pd
import func as f
import math as m
from io import StringIO

'''
# Footbridge-Vibrations


'''

"## Import Files"
"### Eigenfrequencies"
eigenfrequencies = st.file_uploader("Import Eigenfrequencies", key='eigen')
if eigenfrequencies is not None:
    freq = f.get_freq(eigenfrequencies)

    col1, col2 = st.columns(2)
    with col1:
        first_lc_empty = st.number_input('First LC of eigenfrequency - empty bridge:', value=7500, step=1)
    with col2:
        first_lc_loaded = st.number_input('First LC of eigenfrequency - loaded bridge:', value=7600, step=1)

    freq_empty = freq[(freq['LC'] < first_lc_loaded)].copy().reset_index()
    freq_loaded = freq[(freq['LC'] >= first_lc_loaded)].copy().reset_index()
    checked_freq = f.check_freq(freq_empty)
    freq_to_calc = checked_freq[(checked_freq.vert_to_check == True) | (checked_freq.hor_to_check == True)]
    st.write('ACCELERATIONS NEED TO BE CHECKED FOR THE FOLLOWING MODES:')
    freq_to_calc


    modal_displacements = st.file_uploader("Import modal displacements", key='modal_disp')
    node_coordinates = st.file_uploader("Import node coordinates", key='node_coord')
    unit_load_Si = st.file_uploader("Import unit load Si", key='Si')
    if modal_displacements is not None and node_coordinates is not None and unit_load_Si is not None:
        col1, col2 = st.columns(2)
        with col1:
            software_scaling_factor = st.selectbox('Software scaling factor', ['Sofistik'], key='software')
            bridge_type = st.selectbox('Bridge Type', [
                'Steel',
                'Steel-Concrete',
                'Reinforced Concrete',
                'Prestressed Concrete',
                'Wood'], key='bridge')
            traffic = st.selectbox('Traffic Type', ['Dense', 'Not Dense'], key='traffic')
        with col2:
            vertical = st.selectbox('Vertical axis', ['x', 'y', 'z'], index=2, key='vert')
            longitudinal = st.selectbox('Longitudinal axis', ['x', 'y', 'z'], index=0, key='long')
            lateral = st.selectbox('Lateral axis', ['x', 'y', 'z'], index=1, key='lat')

        # Calculation
        if software_scaling_factor == "Sofistik":
            factor_scaling = 0.001 / m.sqrt(1000)  # Scaling factor for Sofistik

        nodes = f.get_nodes(node_coordinates)
        Si = f.get_Si(unit_load_Si)
        nodes = f.merge_nodes(nodes, Si)

        modal_disp = f.get_modal_disp(modal_displacements)
        modal_disp = f.scale_modal_disp(modal_disp, factor_scaling)
        modal_disp_empty = modal_disp[(modal_disp['LC'] < first_lc_loaded)].copy().reset_index()
        modal_disp_loaded = modal_disp[(modal_disp['LC'] >= first_lc_loaded)].copy().reset_index()
        S_total = nodes.Si.sum()

        n_lc = freq_to_calc['LC'].count()

        results_mode = []
        for mode_id in freq_to_calc.index.array:
            # Check mode
            mode = mode_id + 1
            mode_lc_empty = first_lc_empty + mode_id
            mode_lc_loaded = first_lc_loaded + mode_id
            mode_f_empty = freq_empty[freq_empty.LC == mode_lc_empty]['f'].item()
            mode_f_loaded = freq_loaded[freq_loaded.LC == mode_lc_loaded]['f'].item()
            # print(f'CHECK MODE {mode} - freq = {mode_f_empty} (empty), {mode_f_loaded} (loaded) :')
            results = pd.DataFrame(columns=['vert1', 'vert2', 'vert3', 'vert4', 'vert5', 'long1', 'long2', 'long3', 'long4', 'long5', 'lat1', 'lat2', 'lat3', 'lat4', 'lat5'])
            results.loc[0] = ['', 'TC 1', 'TC 2', 'TC 3', 'TC 4', '', 'TC 1', 'TC 2', 'TC 3', 'TC 4', '', 'TC 1',
                              'TC 2', 'TC 3', 'TC 4']
            for i in range(1, 15):
                results.loc[i] = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
            results.iloc[1:, 0] = ['d (p/m2)',
                                   'N (-)',
                                   'N_lim (-)',
                                   '<5% modal mass?',
                                   'Modal mass',
                                   'Load',
                                   'Damping (%)',
                                   'Neq (-)',
                                   'gamma P (N)',
                                   'q_eq',
                                   'a_max',
                                   'a_lim',
                                   'is acceptable?',
                                   'm_tmd'
                                   ]

            index = 1
            for dir in ['vertical', 'longitudinal', 'lateral']:
                axis = f.get_axis(dir, vertical, longitudinal, lateral)
                for TC in range(1, 5):
                    d = f.get_d(TC, S_total)
                    N = d * S_total

                    disp = modal_disp_empty[modal_disp_empty.LC == mode_lc_empty]
                    # Check if pedestrian loads need to be considered
                    mj = f.get_modal_mass(disp, axis)
                    N_limit = 0.05 * mj / 70

                    if N > N_limit:
                        is_less_5pc = False
                        load = 'loaded'
                        disp = modal_disp_loaded[modal_disp_loaded.LC == mode_lc_loaded]
                        mode_f = mode_f_loaded
                    else:
                        is_less_5pc = True
                        load = 'empty'
                        mode_f = mode_f_empty

                    damping = f.get_damping(TC, bridge_type)
                    N_eq = f.get_N_eq(N, damping, d)
                    gp = f.get_gp(mode_f, dir)
                    q_eq = N_eq / S_total * gp

                    table_mode = f.merge_all_mode(disp, nodes)
                    sum_si_disp_df = abs(table_mode[axis]) * table_mode['Si']
                    sum_si_disp = sum_si_disp_df.sum()
                    max_disp = abs(table_mode[axis]).max()
                    a_max = q_eq * sum_si_disp / (2 * damping) * max_disp

                    a_req = f.get_a_req(dir, TC, traffic)
                    is_ok = a_max < a_req

                    if is_ok:
                        m_tmd = '-'
                    else:
                        a_new = a_max
                        damping_new = damping
                        while a_new > a_req:
                            damping_new += 0.00001
                            N_eq_new = f.get_N_eq(N, damping_new, d)
                            q_eq_new = N_eq_new / S_total * gp
                            a_new = q_eq_new * sum_si_disp / (2 * damping_new) * max_disp
                        damping_eff = damping
                        m_tmd = 0
                        while damping_eff < damping_new:
                            m_tmd += 1
                            mu = m_tmd / mj
                            damping_eff = damping + (2 * m.sqrt(2 / (mu * (1 + mu)))) ** -1

                    results.iloc[1:, index] = [d, N, N_limit, is_less_5pc, mj, load, damping * 100, N_eq, gp, q_eq,
                                               a_max, a_req, is_ok, m_tmd]

                    index += 1
                index += 1

            results_mode.append(results)
            # print(results[:][:])
            # print('')

        mode_list = freq_to_calc.index.array + 1
        mode_list_str = [str(x) for x in mode_list]
        mose_list_int = [int(x) for x in mode_list]

        mode = st.selectbox('Select mode', mode_list_str, index=0, key='mode')
        mode_id = int(mode) - 1
        mode_lc_empty = first_lc_empty + mode_id
        mode_lc_loaded = first_lc_loaded + mode_id
        mode_f_empty = freq_empty[freq_empty.LC == mode_lc_empty]['f'].item()
        mode_f_loaded = freq_loaded[freq_loaded.LC == mode_lc_loaded]['f'].item()
        st.write(f'CHECK MODE {mode} - freq = {mode_f_empty} (empty), {mode_f_loaded} (loaded) :')
        st.dataframe(results_mode[mode_id],
                     column_config={
                         "d (p/m2)": st.column_config.NumberColumn(format="{:.2f}")
                     },
                     hide_index=True)
        csv = results_mode[mode_id].to_csv(index=False).encode('utf-8')
        st.download_button(label="Download", data=csv, file_name=f'mode {mode}.csv', mime="text/csv")


