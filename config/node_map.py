# node_map.py

# Mapping of friendly names (used by API) to actual OPC UA Node IDs
NODES = {

    # DOOSAN COBOT CONTROLLER
    "dcob_joint6_angle":"ns=3;s=|var|Nerve.Application.PLC_PRG.joint6_angle",
    "dcob_servostatus":"ns=3;s=|var|Nerve.Application.PLC_PRG.doosan_servostatus",
    "dcob_homeAlreadyChecked":"ns=3;s=|var|Nerve.Application.PLC_PRG.homeAlreadyChecked",
    "dcob_intOutput0":"ns=3;s=|var|Nerve.Application.PLC_PRG.intOutput0",
    "dcob_intOutput1":"ns=3;s=|var|Nerve.Application.PLC_PRG.intOutput1",
    "dcob_joint5_angle":"ns=3;s=|var|Nerve.Application.PLC_PRG.joint5_angle",
    "dcob_boolOutput1":"ns=3;s=|var|Nerve.Application.PLC_PRG.boolOutput1",
    "dcob_boolOutput2":"ns=3;s=|var|Nerve.Application.PLC_PRG.boolOutput2",
    "dcob_floatInput0":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatInput0",
    "dcob_floatInput1":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatInput1",
    "dcob_isHome":"ns=3;s=|var|Nerve.Application.PLC_PRG.isHome",
    "dcob_floatOutput0":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatOutput0",
    "dcob_floatOutput1":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatOutput1",
    "dcob_floatOutput2":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatOutput2",
    "dcob_floatOutput3":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatOutput3",
    "dcob_floatOutput4":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatOutput4",
    "dcob_floatOutput5":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatOutput5",
    "dcob_floatOutput6":"ns=3;s=|var|Nerve.Application.PLC_PRG.floatOutput6",
    "dcob_man_height":"ns=3;s=|var|Nerve.Application.PLC_PRG.man_height",
    "dcob_joint4_angle":"ns=3;s=|var|Nerve.Application.PLC_PRG.joint4_angle",
    "dcob_standalone_running":"ns=3;s=|var|Nerve.Application.PLC_PRG.STANDALONE_RUNNING",
    "dcob_ee_grip_off":"ns=3;s=|var|Nerve.Application.PLC_PRG.Dout10_bit_EEgripOFF",
    "dcob_man_height_profinet":"ns=3;s=|var|Nerve.Application.PLC_PRG.man_height_profinet",
    "dcob_robotResumeOperation":"ns=3;s=|var|Nerve.Application.PLC_PRG.robotResumeOperation",
    "dcob_height":"ns=3;s=|var|Nerve.Application.PLC_PRG.height",
    "dcob_emergency_stop":"ns=3;s=|var|Nerve.Application.PLC_PRG.EMERGENCY_STOP",
    "dcob_joint3_angle":"ns=3;s=|var|Nerve.Application.PLC_PRG.joint3_angle",
    "dcob_state":"ns=3;s=|var|Nerve.Application.PLC_PRG.doosan_state",
    "dcob_interrupted":"ns=3;s=|var|Nerve.Application.PLC_PRG.INTERRUPTED",
    "dcob_manual_standby":"ns=3;s=|var|Nerve.Application.PLC_PRG.MANUAL_STANDBY",
    "dcob_joint2_angle":"ns=3;s=|var|Nerve.Application.PLC_PRG.joint2_angle",
    "dcob_robotInPosition":"ns=3;s=|var|Nerve.Application.PLC_PRG.robotInPosition",
    "dcob_standalone_standby":"ns=3;s=|var|Nerve.Application.PLC_PRG.STANDALONE_STANDBY",
    "dcob_boolInput1":"ns=3;s=|var|Nerve.Application.PLC_PRG.boolInput1",
    "dcob_boolInput2":"ns=3;s=|var|Nerve.Application.PLC_PRG.boolInput2",
    "dcob_wagoDigitalOut10":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut10",
    "dcob_wagoDigitalOut1":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut1",
    "dcob_wagoDigitalOut2":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut2",
    "dcob_wagoDigitalOut3":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut3",
    "dcob_wagoDigitalOut4":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut4",
    "dcob_wagoDigitalOut5":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut5",
    "dcob_wagoDigitalOut6":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut6",
    "dcob_wagoDigitalOut7":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut7",
    "dcob_wagoDigitalOut8":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut8",
    "dcob_wagoDigitalOut9":"ns=3;s=|var|Nerve.Application.PLC_PRG.wagoDigitalOut9",
    "dcob_joint1_angle":"ns=3;s=|var|Nerve.Application.PLC_PRG.joint1_angle",
    "dcob_ee_grip_on":"ns=3;s=|var|Nerve.Application.PLC_PRG.Dout9_bit_EEgripON",
    "dcob_safe_off":"ns=3;s=|var|Nerve.Application.PLC_PRG.SAFE_OFF",
    "dcob_intInput0":"ns=3;s=|var|Nerve.Application.PLC_PRG.intInput0",
    "dcob_intInput1":"ns=3;s=|var|Nerve.Application.PLC_PRG.intInput1",
    "dcob_notRunning":"ns=3;s=|var|Nerve.Application.PLC_PRG.notRunning",

    # SEIT INDUCTION HEATING MACHINE
    "seit_targetTempInduction":"ns=3;s=|var|Nerve.Application.GlobalVariables.targetTempInduction",
    "seit_enablePlcInductionControl":"ns=3;s=|var|Nerve.Application.GlobalVariables.enablePlcInductionControl",
    "seit_enableFirstInduction":"ns=3;s=|var|Nerve.Application.GlobalVariables.enableFirstInduction",
    "seit_currentTempMaxValueReading":"ns=3;s=|var|Nerve.Application.GlobalVariables.currentTempMaxValueReading",

    # MULLUTENSIL DISASSEMBLY MACHINE
    # asse X
    "mill_axis_x_acc":'ns=4;s="DB AXIS X"."ACC"',
    "mill_axis_x_dec":'ns=4;s="DB AXIS X"."DEC"',
    "mill_axis_x_pos_attuale":'ns=4;s="DB AXIS X"."POS_ATTUALE"',
    "mill_axis_x_vel":'ns=4;s="DB AXIS X"."VELOCITA_ALTA"',
    "mill_axis_x_step":'ns=4;s="DB AXIS X"."HMI"."PL_STEP"',
    "mill_axis_x_pos_step":'ns=4;s="DB AXIS X"."HMI"."POS_STEP"',

    # asse Y 
    "mill_axis_y_acc":'ns=4;s="DB AXIS Y"."ACC"',
    "mill_axis_y_dec":'ns=4;s="DB AXIS Y"."DEC"',
    "mill_axis_y_pos_attuale":'ns=4;s="DB AXIS Y"."POS_ATTUALE"',
    "mill_axis_y_vel":'ns=4;s="DB AXIS Y"."VELOCITA_ALTA"',
    "mill_axis_y_step":'ns=4;s="DB AXIS Y"."HMI"."PL_STEP"',
    "mill_axis_y_pos_step":'ns=4;s="DB AXIS Y"."HMI"."POS_STEP"',

    # asse Z 
    "mill_axis_z_acc":'ns=4;s="DB AXIS Z"."ACC"',
    "mill_axis_z_dec":'ns=4;s="DB AXIS Z"."DEC"',
    "mill_axis_z_pos_attuale":'ns=4;s="DB AXIS Z"."POS_ATTUALE"',
    "mill_axis_z_vel":'ns=4;s="DB AXIS Z"."VELOCITA_ALTA"',
    "mill_axis_z_step":'ns=4;s="DB AXIS Z"."HMI"."PL_STEP"',
    "mill_axis_z_pos_step":'ns=4;s="DB AXIS Z"."HMI"."POS_STEP"',

    # asse 360 
    "mill_axis_360_acc":'ns=4;s="DB AXIS 360"."ACC"',
    "mill_axis_360_dec":'ns=4;s="DB AXIS 360"."DEC"',
    "mill_axis_360_pos_attuale":'ns=4;s="DB AXIS 360"."POS_ATTUALE"',
    "mill_axis_360_vel":'ns=4;s="DB AXIS 360"."VELOCITA_ALTA"',
    "mill_axis_360_step":'ns=4;s="DB AXIS 360"."HMI"."PL_STEP"',
    "mill_axis_360_pos_step":'ns=4;s="DB AXIS 360"."HMI"."POS_STEP"',

    # asse PRS 
    "mill_axis_prs_acc":'ns=4;s="DB AXIS PRS"."ACC"',
    "mill_axis_prs_dec":'ns=4;s="DB AXIS PRS"."DEC"',
    "mill_axis_prs_pos_attuale":'ns=4;s="DB AXIS PRS"."POS_ATTUALE"',
    "mill_axis_prs_vel":'ns=4;s="DB AXIS PRS"."VELOCITA_ALTA"',
    "mill_axis_prs_step":'ns=4;s="DB AXIS PRS"."HMI"."PL_STEP"',
    "mill_axis_prs_pos_step":'ns=4;s="DB AXIS PRS"."HMI"."POS_STEP"',

    # aria, sensori e porte 
    "mill_hmi_aria_alza_sensore":'ns=4;s="PL_HMI_ARIA"."ALZA_SENSORE"',
    "mill_hmi_aria_abb_sensore":'ns=4;s="PL_HMI_ARIA"."ABB_SENSORE"',
    "mill_hmi_aria_apri_griffe":'ns=4;s="PL_HMI_ARIA"."APRI_GRIFFE"',
    "mill_hmi_aria_chiudi_griffe":'ns=4;s="PL_HMI_ARIA"."CHIUDI_GRIFFE"',
    "mill_hmi_aria_alza_index":'ns=4;s="PL_HMI_ARIA"."ALZA_INDEX"',
    "mill_hmi_aria_abb_index":'ns=4;s="PL_HMI_ARIA"."ABB_INDEX"',
    "mill_hmi_aria_apre_pinze_man":'ns=4;s="PL_HMI_ARIA"."APRE_PINZE_MAN"',
    "mill_hmi_aria_chiude_pinze_man":'ns=4;s="PL_HMI_ARIA"."CHIUDE_PINZE_MAN"',
    "mill_hmi_aria_alza_porta_2":'ns=4;s="PL_HMI_ARIA"."ALZA_PORTA_2"',
    "mill_hmi_aria_abb_porta_2":'ns=4;s="PL_HMI_ARIA"."ABB_PORTA_2"',
    "mill_hmi_aria_alza_porta_3":'ns=4;s="PL_HMI_ARIA"."ALZA_PORTA_3"',
    "mill_hmi_aria_abb_porta_3":'ns=4;s="PL_HMI_ARIA"."ABB_PORTA_3"',
    # aria barr_back (pos1 = abbassata/attiva, pos0 = alzata/disattiva)
    # pos_attiva non ancora disponibile — aggiungere quando i sensori di posizione saranno cablati
    "mill_air_barr_b_pos1_step":'ns=4;s="PL_HMI_ARIA"."ABB_PORTA_1"',
    "mill_air_barr_b_pos0_step":'ns=4;s="PL_HMI_ARIA"."ALZA_PORTA_1"',
    # aria avvitatore
    "mill_air_avv_pos0_step":'ns=4;s="PL_HMI_ARIA"."DX_AVV"',
    "mill_air_avv_pos1_step":'ns=4;s="PL_HMI_ARIA"."SX_AVV"',
    "mill_air_avv_pos1_attiva":'ns=4;s="IN_PLC"."42SQ9"',
    "mill_air_avv_pos0_attiva":'ns=4;s="IN_PLC"."42SQ10"',

    # SENSORI E PLC INPUTS 
    "mill_pos_SENSup":'ns=4;s="IN_PLC"."44SQ21"',
    "mill_pos_DoorsDxON":'ns=4;s="88S1 CH1"',
    "mill_pos_BarrFrontON":'ns=4;s="88S2 CH1"',
    "mill_pos_BarrSideON":'ns=4;s="88S3 CH1"',
    "mill_pos_DoorsSxON":'ns=4;s="88S4 CH1"',
    "mill_SENSPOS_BarrBackON":'ns=4;s="RX1"',
    "mill_carico":'ns=4;s="DB ANIM"."PESO CELLA"'

}

def get_node_id(name: str) -> str | None:
    """Safely retrieve a node ID by friendly name."""
    return NODES.get(name)