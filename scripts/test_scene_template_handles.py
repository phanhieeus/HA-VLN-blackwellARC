from pathlib import Path
import ast
import os
import habitat_sim

p=Path(__file__).resolve().parents[1]/'HASimulator/environments.py'
tree=ast.parse(p.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='HAVLNCE')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_register_motion_templates')
scope={'os':os}
exec(compile(ast.Module(body=[method],type_ignores=[]),str(p),'exec'),scope)
Adapter=type('Adapter',(),{'_register_motion_templates':scope['_register_motion_templates']})
cfg=habitat_sim.SimulatorConfiguration();cfg.scene_id='NONE';cfg.create_renderer=False
agent=habitat_sim.agent.AgentConfiguration();agent.sensor_specifications=[]
sim=habitat_sim.Simulator(habitat_sim.Configuration(cfg,[agent]))
obj=Adapter();obj.obj_templates_mgr=sim.get_object_template_manager()
obj.data_path=str(Path(__file__).resolve().parents[1]/'Data/HAPS2_0');obj._motion_template_handles={}
folders=[p for p in sorted(Path(obj.data_path).iterdir()) if p.is_dir()][:2]
for folder in folders:
    handles=obj._register_motion_templates(folder.name)
    assert len(handles)==120
    for frame,handle in handles.items():
        assert Path(handle).resolve()==(folder/f'frame{frame:03d}.object_config.json').resolve()
    before=obj.obj_templates_mgr.get_num_templates()
    assert obj._register_motion_templates(folder.name) is handles
    assert obj.obj_templates_mgr.get_num_templates()==before
print('EXACT_NATIVE_FRAME_HANDLES_AND_REUSE_VERIFIED',len(folders)*120,flush=True)
sim.close()
