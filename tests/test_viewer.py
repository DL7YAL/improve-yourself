import json
import re
import pytest
from dataclasses import replace
from pathlib import Path
from improve_yourself.replay_controller import ReplayController
from improve_yourself.viewer import render_viewer, render_viewer_state, visible_players_at_frame, world_to_radar, viewer_state
from test_replay_controller import _store

def test_projection_and_dead_filter():
 assert world_to_radar(-3230,1713,-3230,1713,5)==(0,0)
 assert [p['player_id'] for p in visible_players_at_frame([{'player_id':'a'},{'player_id':'d','alive':False}])]==['a']

def test_view_mode_changes_presentation_only(tmp_path):
 store=_store(tmp_path); controller=ReplayController(store); controller.seek_scene('scene-1'); before=controller.snapshot(); controller.set_view_mode('first_person'); after=controller.snapshot()
 assert (after.current_round,after.requested_tick,after.resolved_tick,after.selected_player_id,after.frame)==(before.current_round,before.requested_tick,before.resolved_tick,before.selected_player_id,before.frame)

def test_frame_tick_mismatch_is_rejected(tmp_path):
 store=_store(tmp_path); context=replace(ReplayController(store).snapshot(), resolved_tick=999)
 with pytest.raises(ValueError, match='frame tick must equal resolved tick'): render_viewer_state(store,context,tmp_path/'bad.html')

def test_background_swap_does_not_mutate_replay_state(tmp_path):
 store=_store(tmp_path); controller=ReplayController(store); context=controller.seek_scene('scene-1'); before=viewer_state(store,context)
 one=tmp_path/'one.svg'; two=tmp_path/'two.svg'; one.write_text('<svg/>'); two.write_text('<svg/>')
 first=render_viewer(store.manifest_path,tmp_path/'one.html',radar_path=one); second=render_viewer(store.manifest_path,tmp_path/'two.html',radar_path=two)
 assert viewer_state(store,context)==before
 assert '"background_kind":"local_override"' in first.read_text() and '"background_kind":"local_override"' in second.read_text()
 assert re.search(r'"state":(\{.*?\}),"transform"',first.read_text()).group(1)==re.search(r'"state":(\{.*?\}),"transform"',second.read_text()).group(1)

def test_ancient_generated_overview_is_not_product_fallback(tmp_path):
 store=_store(tmp_path); store.manifest['source']['map_id']='de_ancient'; store.manifest_path.write_text(json.dumps(store.manifest))
 result=render_viewer(store.manifest_path,tmp_path/'viewer.html'); text=result.read_text()
 assert '"background_kind":"product_map_unavailable"' in text
 assert '"background_available":false' in text
 assert 'PRODUCT_MAP_UNAVAILABLE' in text
 source=(Path(__file__).parents[1]/'src/improve_yourself/viewer.py').read_text()
 assert 'resources/generated_overviews' not in source

def test_explicit_background_still_works(tmp_path):
 store=_store(tmp_path); background=tmp_path/'approved.svg'; background.write_text('<svg/>')
 result=render_viewer(store.manifest_path,tmp_path/'viewer.html',radar_path=background).read_text()
 assert '"background_kind":"local_override"' in result
 assert '"background_available":true' in result
 assert 'data:image/svg+xml;base64' in result

def test_canvas_yaw_and_missing_background_are_honest(tmp_path):
 store=_store(tmp_path); store.manifest['source']['map_id']='de_ancient'; store.manifest_path.write_text(json.dumps(store.manifest))
 result=render_viewer(store.manifest_path,tmp_path/'viewer.html'); text=result.read_text()
 assert 'M.canvas' in text and "className='dir'" in text
 assert '10.24' not in (Path(__file__).parents[1]/'src/improve_yourself/viewer.py').read_text()
 assert '"background_available":false' in text

def test_wrong_schema_and_script_escape(tmp_path):
 bad=tmp_path/'bad.json'; bad.write_text('{"schema":"bad"}')
 with pytest.raises(ValueError): render_viewer(bad,tmp_path/'out.html')
 legacy=tmp_path/'legacy.json'; hostile='</script><script>alert(1)</script>'; legacy.write_text(json.dumps({'schema':'iy.replay/v1','map_name':'de_x','coordinate_space':'cs2_world','scenes':[{'round_number':1,'frames':[{'tick':1,'players':[{'name':hostile}]}]}]}))
 html=render_viewer(legacy,tmp_path/'legacy.html').read_text(); assert hostile not in html and '\\u003c/script>' in html
 with pytest.raises(ValueError): render_viewer(legacy,tmp_path/'badscale.html',scale=0)

def test_legacy_and_v2_models_satisfy_js_contract(tmp_path):
 store=_store(tmp_path); v2=render_viewer(store.manifest_path,tmp_path/'v2.html').read_text()
 legacy=tmp_path/'legacy.json'; legacy.write_text(json.dumps({'schema':'iy.replay/v1','map_name':'de_x','coordinate_space':'cs2_world','scenes':[{'round_number':1,'frames':[{'tick':1,'players':[]}]}]})); old=render_viewer(legacy,tmp_path/'old.html').read_text()
 for text in (v2,old):
  for key in ('"canvas"','"background_available"','"transform"','"requested_tick"','"resolved_tick"','"selected_player_id"','"view_mode"'): assert key in text
