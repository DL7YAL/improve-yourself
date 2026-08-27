import json
from tools.map_generator.project import load_projection, project

def test_uses_existing_verified_projection(tmp_path):
    path=tmp_path/'map.json'; path.write_text(json.dumps({'schema':'iy.map_overview_metadata/v1','map_id':'de_test','canvas':{'width':100,'height':100},'transform':{'origin_world':{'x':0,'y':100},'world_units_per_pixel':1,'rotation_deg_clockwise':0,'verification_status':'VERIFIED'}}))
    assert project(load_projection(path), 20, 70)==(20,30)
