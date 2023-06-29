import pandas as pd
import math as m
import streamlit as st


def get_freq(file):
    df = pd.read_csv(file)
    df.columns = ['LC', 'Title', 'f']
    return df


def check_freq(df_in):
    df = df_in
    f_min = df_in.f.min()
    if f_min > 5:
        df['vert_to_check'] = False
    else:
        vert = (1.7 < df.f) & (df.f < 2.2)
        df['vert_to_check'] = vert

    hor = (0.3 < df.f) & (df.f < 2.5)
    df['hor_to_check'] = hor

    return df


def get_nodes(file):
    df = pd.read_csv(file)
    df.columns = ['NODE', 'X', 'Y', 'Z']
    return df


def get_Si(file):
    df = pd.read_csv(file)
    df.columns = ['NODE', 'Si']
    df['Si'] = df['Si'].astype(float)
    df['Si'] = abs(df['Si'])
    return df


def merge_nodes(nodes, Si):
    df = pd.merge(nodes, Si, on='NODE')
    return df


def get_modal_disp(file):
    df = pd.read_csv(file, low_memory=False)
    df.columns = ['LC', 'Title', 'NODE', 'ux', 'uy', 'uz']
    return df


def scale_modal_disp(modal_disp, factor):
    df = modal_disp
    df['sc_ux'] = modal_disp['ux'] * factor
    df['sc_uy'] = modal_disp['uy'] * factor
    df['sc_uz'] = modal_disp['uz'] * factor
    return df


def get_axis(dir, vertical, longitudinal, lateral):
    if vertical == 'x':
        vertical = 'sc_ux'
    elif vertical == 'y':
        vertical = 'sc_uy'
    elif vertical == 'z':
        vertical = 'sc_uz'
    if longitudinal == 'x':
        longitudinal = 'sc_ux'
    elif longitudinal == 'y':
        longitudinal = 'sc_uy'
    elif longitudinal == 'z':
        longitudinal = 'sc_uz'
    if lateral == 'x':
        lateral = 'sc_ux'
    elif lateral == 'y':
        lateral = 'sc_uy'
    elif lateral == 'z':
        lateral = 'sc_uz'

    if dir == 'vertical':
        return vertical
    elif dir == 'longitudinal':
        return longitudinal
    elif dir == 'lateral':
        return lateral


def get_d(TC, S):
    if TC == 1:
        d = 15 / S
    elif TC == 2:
        d = 0.2
    elif TC == 3:
        d = 0.5
    elif TC == 4:
        d = 1
    return d


def get_modal_mass(disp, axis):
    max_disp_all = max(abs(disp[axis].max()),
                       abs(disp[axis].min())
                       )
    modal_mass = 1 / (max_disp_all ** 2)
    return modal_mass


def get_damping(TC, bridge_type):
    values = pd.DataFrame(
        {'type': ['Reinforced Concrete',
                  'Prestressed Concrete',
                  'Steel-Concrete',
                  'Steel',
                  'Wood'],
         '<1p/m2': [0.008, 0.005, 0.003, 0.002, 0.010],
         '>=1p/m2': [0.016, 0.010, 0.006, 0.004, 0.020]
         })
    if TC == 4:
        col = '>=1p/m2'
    else:
        col = '<1p/m2'
    return values[values.type == bridge_type][col].item()


def get_N_eq(N, damping, d):
    if d < 1:
        return 10.8 * m.sqrt(damping * N)
    else:
        return 1.85 * m.sqrt(N)


def get_gp(f, direction, phase='design'):
    if direction == 'vertical':
        if phase == 'design':
            if f <= 0.5:
                gp = 0
            elif f <= 1.3:
                gp = 0 + (280 - 0) * (f - 0.5) / (1.3 - 0.5)
            elif f <= 2.4:
                gp = 280
            elif f <= 3:
                gp = 280 + (70 - 280) * (f - 2.4) / (3 - 2.4)
            elif f <= 4.8:
                gp = 70
            elif f <= 6:
                gp = 70 + (0 - 70) * (f - 4.8) / (6 - 4.8)
            else:
                gp = 0
        else:
            if f <= 1:
                gp = 0
            elif f <= 1.6:
                gp = 0 + (280 - 0) * (f - 1) / (1.6 - 1)
            elif f <= 2.1:
                gp = 280
            elif f <= 2.55:
                gp = 280 + (35 - 280) * (f - 2.1) / (2.55 - 2.1)
            elif f <= 2.95:
                gp = 35
            elif f <= 3.4:
                gp = 35 + (70 - 35) * (f - 2.95) / (3.4 - 2.95)
            elif f <= 4.25:
                gp = 70
            elif f <= 5:
                gp = 70 + (0 - 70) * (f - 4.25) / (5 - 4.25)
            else:
                gp = 0
    if direction == 'longitudinal':
        if phase == 'design':
            if f <= 0.5:
                gp = 0
            elif f <= 1.3:
                gp = 0 + (140 - 0) * (f - 0.5) / (1.3 - 0.5)
            elif f <= 2.4:
                gp = 140
            elif f <= 3:
                gp = 140 + (35 - 140) * (f - 2.4) / (3 - 2.4)
            elif f <= 4.8:
                gp = 35
            elif f <= 6:
                gp = 35 + (0 - 35) * (f - 4.8) / (6 - 4.8)
            else:
                gp = 0
        else:
            if f <= 1:
                gp = 0
            elif f <= 1.6:
                gp = 0 + (140 - 0) * (f - 1) / (1.6 - 1)
            elif f <= 2.1:
                gp = 140
            elif f <= 2.55:
                gp = 140 + (17.5 - 140) * (f - 2.1) / (2.55 - 2.1)
            elif f <= 2.95:
                gp = 17.5
            elif f <= 3.4:
                gp = 17.5 + (35 - 17.5) * (f - 2.95) / (3.4 - 2.95)
            elif f <= 4.25:
                gp = 35
            elif f <= 5:
                gp = 35 + (0 - 35) * (f - 4.25) / (5 - 4.25)
            else:
                gp = 0
    if direction == 'lateral':
        if phase == 'design':
            if f <= 0.15:
                gp = 0
            elif f <= 0.4:
                gp = 0 + (35 - 0) * (f - 0.15) / (0.4 - 0.15)
            elif f <= 1.2:
                gp = 35
            elif f <= 1.4:
                gp = 35 + (7 - 35) * (f - 1.2) / (1.4 - 1.2)
            elif f <= 2.4:
                gp = 7
            elif f <= 2.8:
                gp = 7 + (0 - 7) * (f - 2.4) / (2.8 - 2.4)
            else:
                gp = 0
        else:
            if f <= 0.3:
                gp = 0
            elif f <= 0.5:
                gp = 0 + (35 - 0) * (f - 0.3) / (0.5 - 0.3)
            elif f <= 1.1:
                gp = 35
            elif f <= 1.3:
                gp = 35 + (3.5 - 35) * (f - 1.1) / (1.3 - 1.1)
            elif f <= 1.45:
                gp = 3.5
            elif f <= 1.7:
                gp = 3.5 + (7 - 3.5) * (f - 1.45) / (1.7 - 1.45)
            elif f <= 2.1:
                gp = 7
            elif f <= 2.5:
                gp = 7 + (0 - 7) * (f - 2.1) / (2.5 - 2.1)
            else:
                gp = 0
    return gp


def merge_all_mode(displ, nodes):
    df = pd.merge(nodes, displ, on='NODE')
    return df


def get_a_req(direction, TC, traffic):
    if traffic == 'Dense':
        values = pd.DataFrame(
            {'TC': [1, 2, 3, 4],
             'vertical': [0.70, 1, 1, 2.5],
             'longitudinal': [0.2, 0.3, 0.3, 0.4],
             'lateral': [0.2, 0.3, 0.3, 0.4]
            }
        )
    else:
        values = pd.DataFrame(
            {'TC': [1, 2, 3, 4],
             'vertical': [0.70, 1, 2.5, 2.5],
             'longitudinal': [0.2, 0.3, 0.4, 0.4],
             'lateral': [0.2, 0.3, 0.4, 0.4]
            }
        )
    return values[values.TC == TC][direction].item()

