import json, struct
from tools.map_generator.generate import generate

def test_svg_and_png_are_deterministic(tmp_path):
    tri=tmp_path/'input.tri'; tri.write_bytes(struct.pack('<9f',10,90,0,20,90,0,10,80,0))
    projection=tmp_path/'projection.json'; projection.write_text(json.dumps({'schema':'iy.map_overview_metadata/v1','map_id':'de_test','canvas':{'width':100,'height':100},'transform':{'origin_world':{'x':0,'y':100},'world_units_per_pixel':1,'rotation_deg_clockwise':0,'verification_status':'VERIFIED'}}))
    style=tmp_path/'style.json'; style.write_text('{"background":"#000000","surface_fill":"#111111","surface_stroke":"#222222","surface_stroke_width":1,"border":"#333333","border_width":1}')
    generate(tri,projection,style,tmp_path/'one',grid_size=10); generate(tri,projection,style,tmp_path/'two',grid_size=10)
    assert (tmp_path/'one/de_test_preview.svg').read_bytes()==(tmp_path/'two/de_test_preview.svg').read_bytes()
    assert (tmp_path/'one/de_test_preview.png').read_bytes()==(tmp_path/'two/de_test_preview.png').read_bytes()
