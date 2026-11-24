"""DAC0830 level-actuated digital buffers; no analog or board-wiring model.

TI SNAS534B pp.5-6,9-11 defines the five control levels. None represents
unknown startup contents. This component has no inferred power-on reset.
"""
from __future__ import annotations
from dataclasses import dataclass


def byte(value):
    if value is not None and (type(value) is not int or not 0 <= value <= 255):
        raise ValueError('DAC data must be a byte or unknown')


@dataclass
class DAC0830:
    input_register: int | None = None
    dac_register: int | None = None

    def __post_init__(self):
        byte(self.input_register);byte(self.dac_register)

    def drive(self,data,*,ile,cs_n,wr1_n,wr2_n,xfer_n):
        byte(data)
        if any(type(v) is not int or v not in (0,1) for v in (ile,cs_n,wr1_n,wr2_n,xfer_n)):
            raise ValueError('DAC controls must be binary levels')
        load=bool(ile and not cs_n and not wr1_n)
        transfer=not wr2_n and not xfer_n
        # Both latches can be open, so a level change propagates through both.
        if load:self.input_register=data
        if transfer:self.dac_register=self.input_register
        return dict(input_register=self.input_register,dac_register=self.dac_register,
                    load_enabled=load,transfer_enabled=transfer)


def replay(trace,config,route_name,transfer_name):
    """Apply an explicitly hypothetical PC-selected Y bus and strobe schedule."""
    if config.get('status')!='hypothesis' or not config.get('evidence'):
        raise ValueError('DAC connection requires hypothesis provenance')
    route=config['routes'][route_name];transfer=config['transfer_modes'][transfer_name]
    pcs=route['pcs']
    if not pcs or len(set(pcs))!=len(pcs) or any(type(p) is not int or not 0<=p<1024 for p in pcs):
        raise ValueError('invalid DAC route PCs')
    if route['source']!='alu_y':raise ValueError('unsupported DAC data source')
    if transfer['when'] not in ('after_each_load','first_pc','never'):
        raise ValueError('unsupported transfer schedule')
    if transfer['when']=='first_pc' and (type(transfer['pc']) is not int or not 0<=transfer['pc']<1024):
        raise ValueError('invalid DAC transfer PC')
    dac=DAC0830(**config['initial']);pins=config['idle_pins'].copy();data=None
    dac.drive(data,**pins)
    events=[];transferred=False
    def pulse(row,signal,label):
        for level in (0,1):
            pins[signal]=level
            state=dac.drive(data,**pins)
            events.append(dict(cycle=row['cycle'],pc=row['pc'],action=label+('-open' if level==0 else '-close'),
                data=data,pins=pins.copy(),**state,status=config['status'],evidence=config['evidence']))
    for row in trace:
        if row['pc'] in pcs:
            data=row['alu']['y'];pulse(row,'wr1_n','load')
            if transfer['when']=='after_each_load':pulse(row,'wr2_n','transfer')
        if transfer['when']=='first_pc' and row['pc']==transfer['pc'] and not transferred:
            pulse(row,'wr2_n','transfer');transferred=True
    return dict(input_register=dac.input_register,dac_register=dac.dac_register,events=events)
