#扣费

xp add @a[team=!,scores={use.silverfish_spawn_egg=1..}] -1 levels

xp add @a[team=!,scores={use.snowball=1..}] -3 levels
xp add @a[team=!,scores={use.arrow=1..}] -1 levels
xp add @a[team=!,scores={use.trident=1..}] -4 levels
xp add @a[team=!,scores={use.spectral_arrow=1..}] -5 levels
xp add @a[team=!,scores={use.ender_pearl=1..}] -2 levels
xp add @a[team=!,scores={use.blaze_spawn_egg=1..}] -4 levels

xp add @a[team=!,scores={use.guardian_spawn_egg=1..}] -2 levels
xp add @a[team=!,scores={use.creeper_spawn_egg=1..}] -3 levels
xp add @a[team=!,scores={use.ghast_spawn_egg=1..}] -4 levels
xp add @a[team=!,scores={use.witch_spawn_egg=1..}] -4 levels
xp add @a[team=!,scores={use.ocelot_spawn_egg=1..}] -3 levels

xp add @a[team=!,scores={use.wither_skeleton_spawn_egg=1..}] -7 levels
xp add @a[team=!,scores={use.parrot_spawn_egg=1..}] -9 levels
xp add @a[team=!,scores={use.phantom_spawn_egg=1..}] -5 levels
xp add @a[team=!,scores={use.squid_spawn_egg=1..}] -4 levels

xp add @a[team=!,scores={use.iron_golem_spawn_egg=1..}] -5 levels
xp add @a[team=!,scores={use.spider_spawn_egg=1..}] -5 levels
xp add @a[team=!,scores={use.cave_spider_spawn_egg=1..}] -4 levels 
xp add @a[team=!,scores={use.zombified_piglin_spawn_egg=1..}] -6 levels
xp add @a[team=!,scores={use.magma_cube_spawn_egg=1..}] -3 levels

#发牌

execute as @a[team=!,scores={use.silverfish_spawn_egg=1..}] run function missile_royale:game/deal/deal

execute as @a[team=!,scores={use.snowball=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.arrow=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.trident=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.spectral_arrow=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.ender_pearl=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.blaze_spawn_egg=1..}] run function missile_royale:game/deal/deal

execute as @a[team=!,scores={use.guardian_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.creeper_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.ghast_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.witch_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.ocelot_spawn_egg=1..}] run function missile_royale:game/deal/deal

execute as @a[team=!,scores={use.wither_skeleton_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.parrot_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.phantom_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.squid_spawn_egg=1..}] run function missile_royale:game/deal/deal

execute as @a[team=!,scores={use.iron_golem_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.spider_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.cave_spider_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.zombified_piglin_spawn_egg=1..}] run function missile_royale:game/deal/deal
execute as @a[team=!,scores={use.magma_cube_spawn_egg=1..}] run function missile_royale:game/deal/deal

#重置道具使用变量

scoreboard players reset @a[team=!] use.silverfish_spawn_egg

scoreboard players reset @a[team=!] use.snowball
scoreboard players reset @a[team=!] use.arrow
scoreboard players reset @a[team=!] use.trident
scoreboard players reset @a[team=!] use.spectral_arrow
scoreboard players reset @a[team=!] use.ender_pearl
scoreboard players reset @a[team=!] use.blaze_spawn_egg
scoreboard players reset @a[team=!] use.guardian_spawn_egg
scoreboard players reset @a[team=!] use.creeper_spawn_egg
scoreboard players reset @a[team=!] use.ghast_spawn_egg
scoreboard players reset @a[team=!] use.witch_spawn_egg
scoreboard players reset @a[team=!] use.ocelot_spawn_egg
scoreboard players reset @a[team=!] use.wither_skeleton_spawn_egg
scoreboard players reset @a[team=!] use.iron_golem_spawn_egg
scoreboard players reset @a[team=!] use.spider_spawn_egg
scoreboard players reset @a[team=!] use.cave_spider_spawn_egg
scoreboard players reset @a[team=!] use.zombified_piglin_spawn_egg
scoreboard players reset @a[team=!] use.magma_cube_spawn_egg
scoreboard players reset @a[team=!] use.phantom_spawn_egg
scoreboard players reset @a[team=!] use.parrot_spawn_egg
scoreboard players reset @a[team=!] use.squid_spawn_egg
