#先清除旧的保存项

function missile_royale:game/choose/remove_saves

#保存玩家卡组

execute if items entity @s hotbar.* minecraft:silverfish_spawn_egg run tag @s add silverfish_spawn_egg

execute if items entity @s hotbar.* minecraft:snowball run tag @s add snowball
execute if items entity @s hotbar.* minecraft:arrow run tag @s add arrow
execute if items entity @s hotbar.* minecraft:trident run tag @s add trident
execute if items entity @s hotbar.* minecraft:spectral_arrow run tag @s add spectral_arrow
execute if items entity @s hotbar.* minecraft:ender_pearl run tag @s add ender_pearl
execute if items entity @s hotbar.* minecraft:blaze_spawn_egg run tag @s add blaze_spawn_egg

execute if items entity @s hotbar.* minecraft:guardian_spawn_egg run tag @s add guardian_spawn_egg
execute if items entity @s hotbar.* minecraft:creeper_spawn_egg run tag @s add creeper_spawn_egg
execute if items entity @s hotbar.* minecraft:ghast_spawn_egg run tag @s add ghast_spawn_egg
execute if items entity @s hotbar.* minecraft:witch_spawn_egg run tag @s add witch_spawn_egg
execute if items entity @s hotbar.* minecraft:ocelot_spawn_egg run tag @s add ocelot_spawn_egg

execute if items entity @s hotbar.* minecraft:wither_skeleton_spawn_egg run tag @s add wither_skeleton_spawn_egg
execute if items entity @s hotbar.* minecraft:squid_spawn_egg run tag @s add squid_spawn_egg
execute if items entity @s hotbar.* minecraft:phantom_spawn_egg run tag @s add phantom_spawn_egg
execute if items entity @s hotbar.* minecraft:parrot_spawn_egg run tag @s add parrot_spawn_egg

execute if items entity @s hotbar.* minecraft:iron_golem_spawn_egg run tag @s add iron_golem_spawn_egg
execute if items entity @s hotbar.* minecraft:spider_spawn_egg run tag @s add spider_spawn_egg
execute if items entity @s hotbar.* minecraft:cave_spider_spawn_egg run tag @s add cave_spider_spawn_egg
execute if items entity @s hotbar.* minecraft:zombified_piglin_spawn_egg run tag @s add zombified_piglin_spawn_egg
execute if items entity @s hotbar.* minecraft:magma_cube_spawn_egg run tag @s add magma_cube_spawn_egg

clear @s
