import json
from pathlib import Path
from improve_yourself.replay_controller import ReplayController
from improve_yourself.viewer import render_viewer, visible_players_at_frame, world_to_radar, viewer_state
from test_replay_controller import _store

def test_projection_and_dead_filter():
 assert world_to_radar(-3230,1713,-3230,1713,5)==(0,0)
 assert [p['player_id'] for p in visible_players_at_frame([{'player_id':'a'},{'player_id':'d','alive':False}])]==['a']

def test_view_mode_changes_presentation_only(tmp_path):
 store=_store(tmp_path); controller=ReplayController(store); controller.seek_scene('scene-1'); before=controller.snapshot(); controller.set_view_mode('first_person'); after=controller.snapshot()
 assert (after.current_round,after.requested_tick,after.resolved_tick,after.selected_player_id,after.frame)==(before.current_round,before.requested_tick,before.resolved_tick,before.selected_player_id,before.frame)

def test_background_swap_does_not_mutate_replay_state(tmp_path):
 store=_store(tmp_path); controller=ReplayController(store); context=controller.seek_scene('scene-1'); before=viewer_state(store,context)
 one=tmp_path/'one.svg'; two=tmp_path/'two.svg'; one.write_text('<svg/>'); two.write_text('<svg/>')
 first=render_viewer(store.manifest_path,tmp_path/'one.html',radar_path=one); second=render_viewer(store.manifest_path,tmp_path/'two.html',radar_path=two)
 assert viewer_state(store,context)==before
 assert '"background_kind":"local_override"' in first.read_text() and '"background_kind":"local_override"' in second.read_text()

def test_ancient_default_background_is_repository_safe(tmp_path):
 store=_store(tmp_path); store.manifest['source']['map_id']='de_ancient'; store.manifest_path.write_text(json.dumps(store.manifest))
 result=render_viewer(store.manifest_path,tmp_path/'viewer.html')
 assert 'improve_generated' in result.read_text() and 'data:image/svg+xml;base64' in result.read_text()
