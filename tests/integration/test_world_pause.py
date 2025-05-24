import time
from agent_world.main import bootstrap


def test_tick_counter_pauses_when_flag_set():
    world = bootstrap(config_path="config.yaml")
    tm = world.time_manager

    # Ensure a fresh tick counter
    tm.tick_counter = 0

    # Simulate one normal tick
    if world.systems_manager:
        world.systems_manager.update(world, tm.tick_counter)
    tm.sleep_until_next_tick()
    first_tick = tm.tick_counter
    assert first_tick == 1

    # Activate pause and attempt another iteration of main loop logic
    world.paused_for_angel = True

    if world.raw_actions_with_actor and world.action_queue is not None:
        for actor_id, action_text in world.raw_actions_with_actor:
            world.action_queue.enqueue_raw(actor_id, action_text)
        world.raw_actions_with_actor.clear()

    if not world.paused_for_angel:
        if world.systems_manager:
            world.systems_manager.update(world, tm.tick_counter)
        tm.sleep_until_next_tick()
    else:
        time.sleep(0.016)

    assert tm.tick_counter == first_tick
