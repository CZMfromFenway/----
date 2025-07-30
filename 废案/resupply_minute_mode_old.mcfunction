#分钟模式下补给道具

#给予导弹
loot give @a[team=green] loot missile_wars:missile_green_all
loot give @a[team=orange] loot missile_wars:missile_orange_all
#若启用防御性道具，则给予玩家防御性道具
execute if score rule.defensiveItems varibles matches 1 run loot give @a[team=!] loot missile_wars:defensive_items_all
#若启用道具上限上限，则检测箭矢再给予
execute if score rule.defensiveItems varibles matches 1 if score rule.itemCap varibles matches 1 run execute as @a[team=!, nbt={Inventory:[{id:"minecraft:arrow"}]}] run tellraw @s [{"text": "你已拥有箭矢，无法重复获得。","color": "red"}]
$execute if score rule.defensiveItems varibles matches 1 if score rule.itemCap varibles matches 1 run execute as @a[team=!, nbt=!{Inventory:[{id:"minecraft:arrow"}]}] run give @s arrow[lore=["{\"text\": \"发射以点燃TNT\",\"color\": \"gray\"}"]] $(n)
#若未启用道具上限，则直接给予箭矢
$execute if score rule.defensiveItems varibles matches 1 if score rule.itemCap varibles matches 0 run give @a[team=!] arrow[lore=["{\"text\": \"发射以点燃TNT\",\"color\": \"gray\"}"]] $(n)

#如果启用道具上限，则剥夺多余道具
execute if score rule.itemCap varibles matches 1 run function missile_wars:game/take