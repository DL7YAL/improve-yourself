import { CSGrenadeType, Instance } from "cs_script/point_script";

const VERSION = "iy-benchmark/v1.1";
const TICK_SECONDS = 1 / 64;
const PASS_SECONDS = 64;
const COOLDOWN_SECONDS = 3;

const TRANSITIONS = [
    {
        from: "nuke_outside", to: "ancient_b", occlusion: "smoke",
        enter: 19.0, swap: 22.0, exit: 24.5,
    },
    {
        from: "ancient_b", to: "inferno_apps_a", occlusion: "flash",
        landmark: "red_room", approach: 38.0, enter: 41.9, swap: 43.0, exit: 44.5,
    },
];

const SCENES = [
    {
        id: "nuke_outside",
        start: 0,
        end: 22,
        cameras: [
            { t: 0, p: [-1400, -700, 240], q: [-600, 0, 72] },
            { t: 4, p: [-1050, -180, 220], q: [-350, 250, 72] },
            { t: 9, p: [-620, 360, 210], q: [100, 600, 80] },
            { t: 15, p: [-80, 690, 250], q: [450, 850, 70] },
            { t: 19, p: [250, 850, 180], q: [650, 1000, 72] },
            { t: 22, p: [470, 980, 125], q: [900, 1120, 70] },
        ],
        botPositions: [
            [-760, -120, 72, 0, 18, 0], [-580, -20, 72, 0, 12, 0],
            [-420, 110, 72, 0, 7, 0], [-270, 240, 72, 0, 2, 0],
            [-80, 360, 72, 0, -5, 0], [250, 780, 72, 0, 190, 0],
            [430, 690, 72, 0, 188, 0], [610, 600, 72, 0, 185, 0],
            [150, 1020, 210, 0, 205, 0], [720, 980, 300, 0, 200, 0],
        ],
    },
    {
        id: "ancient_b",
        start: 22,
        end: 43,
        cameras: [
            { t: 22, p: [0, 1550, 160], q: [430, 1690, 72] },
            { t: 22.35, p: [0, 1580, 165], q: [0, 2000, 72] },
            { t: 27, p: [0, 2050, 165], q: [0, 2400, 60] },
            { t: 33, p: [0, 2450, 230], q: [0, 2700, 80] },
            { t: 38, p: [0, 2720, 165], q: [0, 2980, 100] },
            { t: 43, p: [0, 2950, 140], q: [0, 3070, 90] },
        ],
        botPositions: [
            [-300, 1900, 72, 0, 90, 0], [0, 2000, 72, 0, 90, 0],
            [300, 2100, 72, 0, 90, 0], [-280, 2300, 72, 0, 90, 0],
            [280, 2400, 72, 0, 90, 0], [-260, 2600, 72, 0, 90, 0],
            [260, 2700, 72, 0, 90, 0], [-220, 2820, 72, 0, 90, 0],
            [0, 2880, 72, 0, 90, 0], [220, 2820, 72, 0, 90, 0],
        ],
    },
    {
        id: "inferno_apps_a",
        start: 43,
        end: 64,
        cameras: [
            { t: 43, p: [0, 3500, 160], q: [0, 3900, 72] },
            { t: 43.35, p: [0, 3520, 165], q: [0, 3900, 90] },
            { t: 44.5, p: [0, 3650, 170], q: [0, 4020, 100] },
            { t: 48, p: [0, 3950, 185], q: [0, 4300, 120] },
            { t: 53, p: [0, 4300, 205], q: [0, 4650, 120] },
            { t: 58, p: [0, 4650, 230], q: [0, 4950, 110] },
            { t: 64, p: [0, 5050, 300], q: [0, 4750, 120] },
        ],
        botPositions: [
            [-300, 3800, 72, 0, 90, 0], [300, 3900, 72, 0, 90, 0],
            [-280, 4100, 96, 0, 90, 0], [280, 4200, 112, 0, 90, 0],
            [-260, 4350, 120, 0, 90, 0], [260, 4500, 120, 0, 90, 0],
            [-240, 4650, 120, 0, 90, 0], [240, 4800, 120, 0, 90, 0],
            [-200, 4950, 120, 0, 90, 0], [200, 5050, 120, 0, 90, 0],
        ],
    },
];

let phase = "waiting";
let phaseStartedAt = 0;
let passStartedAt = 0;
let activePass = "";
let eventIndex = 0;
let activeScene = "";
let cameraPawn;
let booted = false;

function vec(values) {
    return { x: values[0], y: values[1], z: values[2] };
}

function ang(values) {
    return { pitch: values[0], yaw: values[1], roll: values[2] };
}

function smoothstep(value) {
    const t = Math.max(0, Math.min(1, value));
    return t * t * (3 - 2 * t);
}

function mix(a, b, amount) {
    return a + (b - a) * amount;
}

function lookAngles(position, target) {
    const dx = target.x - position.x;
    const dy = target.y - position.y;
    const dz = target.z - position.z;
    const horizontal = Math.sqrt(dx * dx + dy * dy);
    return {
        pitch: -Math.atan2(dz, horizontal) * 180 / Math.PI,
        yaw: Math.atan2(dy, dx) * 180 / Math.PI,
        roll: 0,
    };
}

function interpolateCamera(scene, time) {
    const frames = scene.cameras;
    for (let index = 0; index < frames.length - 1; index++) {
        const from = frames[index];
        const to = frames[index + 1];
        if (time <= to.t) {
            const amount = smoothstep((time - from.t) / (to.t - from.t));
            const position = {
                x: mix(from.p[0], to.p[0], amount),
                y: mix(from.p[1], to.p[1], amount),
                z: mix(from.p[2], to.p[2], amount),
            };
            const target = {
                x: mix(from.q[0], to.q[0], amount),
                y: mix(from.q[1], to.q[1], amount),
                z: mix(from.q[2], to.q[2], amount),
            };
            return { position, angles: lookAngles(position, target) };
        }
    }
    const last = frames[frames.length - 1];
    const position = vec(last.p);
    return { position, angles: lookAngles(position, vec(last.q)) };
}

function command(value, clientOnly = false) {
    if (!clientOnly) Instance.ServerCommand(value);
    Instance.ClientCommand(0, value);
}

function marker(value) {
    command(`echo "[IYBENCH] ${value}"`, true);
    Instance.Msg(`[IYBENCH] ${value}`);
}

function transitionMarker(index, phaseName) {
    const transition = TRANSITIONS[index];
    const landmark = transition.landmark ? ` landmark=${transition.landmark}` : "";
    marker(
        `TRANSITION_${phaseName} from=${transition.from} to=${transition.to}`
        + ` occlusion=${transition.occlusion}${landmark}`
    );
}

function runtimeError(scope, error) {
    Instance.Msg(`[IYBENCH] ERROR scope=${scope} detail=${String(error)}`);
}

function findCameraPawn() {
    const controller = Instance.GetPlayerController(0);
    if (!controller || controller.IsBot()) return undefined;
    return controller.GetPlayerPawn();
}

function hideCameraPawn(pawn) {
    pawn.SetHealth(500);
    pawn.SetArmor(100);
    pawn.DestroyWeapons();
    Instance.EntFireAtTarget({ target: pawn, input: "SetRenderAlpha", value: 0 });
    Instance.EntFireAtTarget({ target: pawn, input: "DisableShadow" });
}

function setupBots() {
    command("bot_kick");
    for (let index = 0; index < 5; index++) command("bot_add_t");
    for (let index = 0; index < 5; index++) command("bot_add_ct");
    command("bot_stop 1");
    command("bot_mimic 1");
    command("bot_mimic_yaw_offset 0");
}

function stageBots(scene) {
    const bots = Instance.GetAllPlayerControllers().filter((controller) => controller.IsBot());
    for (let index = 0; index < bots.length && index < scene.botPositions.length; index++) {
        const pawn = bots[index].GetPlayerPawn();
        const pose = scene.botPositions[index];
        if (!pawn || !pose) continue;
        pawn.SetHealth(500);
        pawn.SetArmor(100);
        if (!pawn.GetActiveWeapon()) pawn.GiveNamedItem(index % 3 === 0 ? "weapon_awp" : "weapon_ak47", true);
        pawn.Teleport({ position: vec(pose), angles: ang(pose.slice(3)), velocity: vec([0, 0, 0]) });
    }
}

function clearUtilities() {
    const classes = [
        "smokegrenade_projectile", "molotov_projectile", "incgrenade_projectile",
        "flashbang_projectile", "hegrenade_projectile", "decoy_projectile",
    ];
    for (const className of classes) {
        for (const entity of Instance.FindEntitiesByClass(className)) entity.Remove();
    }
}

function grenade(type, position, velocity = [0, 0, 0], detonate = true) {
    const projectile = Instance.SpawnGrenadeProjectile({
        type,
        position: vec(position),
        angles: ang([0, 0, 0]),
        velocity: vec(velocity),
        angularVelocity: vec([0, 0, 0]),
    });
    if (detonate) projectile.Detonate();
}

function startFire() {
    command("+attack", true);
}

function stopFire() {
    command("-attack", true);
}

function whiteFadeOut() {
    command("fadeout 0.15 1.4 255 255 255 255", true);
}

function whiteFadeIn() {
    command("fadein 0.35 255 255 255 255", true);
}

function redRoomTint() {
    command("fadeout 0.25 3.3 160 0 0 96", true);
}

function clearRedRoomTint() {
    command("fadein 0.1 160 0 0 96", true);
}

function bombTick() {
    Instance.EntFireAtName({ name: "iy_bomb_tick", input: "StartSound" });
}

const EVENTS = [
    { t: 0.2, run: () => stageBots(SCENES[0]) },
    { t: 1.0, run: () => grenade(CSGrenadeType.SMOKE, [-300, 1100, 82]) },
    { t: 1.35, run: () => grenade(CSGrenadeType.SMOKE, [0, 1160, 82]) },
    { t: 1.7, run: () => grenade(CSGrenadeType.SMOKE, [300, 1220, 82]) },
    { t: 3.2, run: () => grenade(CSGrenadeType.MOLOTOV, [80, 850, 78]) },
    { t: 5.2, run: startFire }, { t: 6.0, run: stopFire },
    { t: 8.2, run: clearUtilities },
    { t: 8.45, run: () => grenade(CSGrenadeType.FLASHBANG, [150, 650, 190]) },
    { t: 13.0, run: startFire }, { t: 14.2, run: stopFire },
    { t: 16.2, run: () => grenade(CSGrenadeType.SMOKE, [200, 920, 82]) },
    { t: 16.45, run: () => grenade(CSGrenadeType.SMOKE, [470, 980, 82]) },
    { t: 16.7, run: () => grenade(CSGrenadeType.SMOKE, [720, 1040, 82]) },
    { t: 19.0, run: () => transitionMarker(0, "ENTER") },
    { t: 21.8, run: () => finishScene("nuke_outside") },
    { t: 22.0, run: () => transitionMarker(0, "SWAP") },

    { t: 22.0, run: () => stageBots(SCENES[1]) },
    { t: 22.05, run: () => grenade(CSGrenadeType.SMOKE, [0, 1550, 160]) },
    { t: 23.0, run: () => grenade(CSGrenadeType.SMOKE, [0, 1800, 85]) },
    { t: 24.0, run: () => grenade(CSGrenadeType.MOLOTOV, [-220, 2400, 75]) },
    { t: 24.5, run: () => transitionMarker(0, "EXIT") },
    { t: 27.0, run: startFire }, { t: 28.4, run: stopFire },
    { t: 31.0, run: () => grenade(CSGrenadeType.HE, [220, 2600, 90]) },
    { t: 34.0, run: startFire }, { t: 35.2, run: stopFire },
    { t: 38.0, run: () => transitionMarker(1, "APPROACH") },
    { t: 38.05, run: redRoomTint },
    { t: 41.82, run: clearRedRoomTint },
    { t: 41.85, run: clearUtilities },
    { t: 41.9, run: () => transitionMarker(1, "ENTER") },
    { t: 41.92, run: () => grenade(CSGrenadeType.FLASHBANG, [0, 2950, 140]) },
    { t: 41.94, run: whiteFadeOut },
    { t: 42.8, run: () => finishScene("ancient_b") },
    { t: 43.0, run: () => transitionMarker(1, "SWAP") },

    { t: 43.0, run: () => stageBots(SCENES[2]) },
    { t: 43.35, run: whiteFadeIn },
    { t: 44.5, run: () => transitionMarker(1, "EXIT") },
    { t: 45.0, run: () => grenade(CSGrenadeType.MOLOTOV, [-180, 4300, 75]) },
    { t: 48.0, run: startFire }, { t: 49.3, run: stopFire },
    { t: 51.0, run: bombTick }, { t: 53.0, run: bombTick },
    { t: 54.5, run: bombTick }, { t: 55.6, run: bombTick },
    { t: 56.4, run: bombTick }, { t: 57.0, run: bombTick },
    { t: 58.0, run: startFire }, { t: 59.2, run: stopFire },
    { t: 60.0, run: bombTick }, { t: 60.4, run: bombTick },
    { t: 60.8, run: bombTick }, { t: 61.2, run: bombTick },
    { t: 62.0, run: () => grenade(CSGrenadeType.HE, [200, 4900, 122]) },
];

function finishScene(sceneId) {
    if (activePass !== "measured") return;
    marker(`REPORT scene=${sceneId}`);
    command("vprof_generate_report", true);
    command("vprof_reset", true);
}

function configure() {
    command("sv_cheats 1");
    command("con_enable 1", true);
    command("con_logfile iy_benchmark_console.log", true);
    command("mp_ignore_round_win_conditions 1");
    command("mp_freezetime 0");
    command("mp_roundtime_defuse 9999");
    command("mp_autoteambalance 0");
    command("mp_limitteams 0");
    command("sv_infinite_ammo 1");
    command("fps_max 0", true);
    command("cl_drawhud 0", true);
    command("r_drawviewmodel 0", true);
    command("cl_showfps 2", true);
    command("cl_frametime_summary_report_detailed 1", true);
    setupBots();
}

function beginPass(name) {
    activePass = name;
    phase = "running";
    passStartedAt = Instance.GetGameTime();
    eventIndex = 0;
    activeScene = "";
    clearUtilities();
    stopFire();
    if (name === "measured") {
        command("vprof_off", true);
        command("vprof_reset", true);
        command("vprof_on", true);
    }
    marker(`PASS_START type=${name} version=${VERSION}`);
}

function endPass() {
    stopFire();
    try {
        clearUtilities();
    } catch (error) {
        runtimeError("end_pass_cleanup", error);
    }
    if (activePass === "warmup") {
        marker("PASS_END type=warmup");
        phase = "cooldown";
        phaseStartedAt = Instance.GetGameTime();
        return;
    }

    marker("REPORT scene=inferno_apps_a");
    try {
        command("vprof_generate_report", true);
        command("vprof_off", true);
    } catch (error) {
        runtimeError("final_report", error);
    }
    marker("PASS_END type=measured status=complete");
    try {
        Instance.SetSaveData(JSON.stringify({ version: VERSION, completedAt: Instance.GetGameTime() }));
    } catch (error) {
        runtimeError("save_result", error);
    }
    command("cl_showfps 0", true);
    command("cl_drawhud 1", true);
    command("r_drawviewmodel 1", true);
    phase = "complete";
}

function updateCamera(elapsed) {
    let scene = SCENES[SCENES.length - 1];
    for (const candidate of SCENES) {
        if (elapsed >= candidate.start && elapsed <= candidate.end) {
            scene = candidate;
            break;
        }
    }
    if (activeScene !== scene.id) {
        activeScene = scene.id;
        marker(`SCENE_START scene=${scene.id} pass=${activePass}`);
    }
    const transform = interpolateCamera(scene, elapsed);
    cameraPawn?.Teleport({
        position: transform.position,
        angles: transform.angles,
        velocity: vec([0, 0, 0]),
    });
}

function think() {
    const now = Instance.GetGameTime();
    try {
        cameraPawn = cameraPawn?.IsValid() ? cameraPawn : findCameraPawn();

        if (!booted && cameraPawn) {
            booted = true;
            hideCameraPawn(cameraPawn);
            configure();
            phase = "boot_delay";
            phaseStartedAt = now;
            marker(`READY version=${VERSION}`);
        }

        if (phase === "boot_delay" && now - phaseStartedAt >= 3) beginPass("warmup");
        if (phase === "cooldown" && now - phaseStartedAt >= COOLDOWN_SECONDS) beginPass("measured");
        if (phase === "running") {
            const elapsed = now - passStartedAt;
            updateCamera(Math.min(elapsed, PASS_SECONDS));
            while (eventIndex < EVENTS.length && EVENTS[eventIndex].t <= elapsed) {
                const event = EVENTS[eventIndex];
                try {
                    event.run();
                } catch (error) {
                    runtimeError(`event_${eventIndex}_at_${event.t}`, error);
                }
                eventIndex++;
            }
            if (elapsed >= PASS_SECONDS) endPass();
        }
    } catch (error) {
        runtimeError("think", error);
    }

    Instance.SetNextThink(Instance.GetGameTime() + TICK_SECONDS);
}

Instance.OnPlayerReset(({ player }) => {
    const controller = player.GetOriginalPlayerController();
    if (!controller.IsBot()) cameraPawn = player;
});
Instance.RegisterCheatCommand("iy_benchmark_status", () => {
    marker(`STATUS phase=${phase} pass=${activePass || "none"} event=${eventIndex}`);
});
Instance.RegisterCheatCommand("iy_benchmark_finish_pass", () => {
    if (phase !== "running") {
        marker(`FINISH_SKIPPED phase=${phase}`);
        return;
    }
    marker(`FINISH_REQUESTED pass=${activePass}`);
    endPass();
});
Instance.OnActivate(() => Instance.SetNextThink(Instance.GetGameTime()));
Instance.OnScriptReload({ after: () => Instance.SetNextThink(Instance.GetGameTime()) });
Instance.SetThink(think);
