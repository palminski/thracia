"""English for everything on the site that is NOT game script:
scene headings, trigger conditions, stage directions and chapter titles.

These are translations of the Japanese transcriber's labels (and of the chapter
titles), written for this site. The dialogue itself is never touched.
"""
import re
import unicodedata

NAMES = {
    "リーフ": "Leif", "フィン": "Finn", "ナンナ": "Nanna", "エーヴェル": "Eyvel", "マリータ": "Mareeta",
    "オーシン": "Osian", "ハルヴァン": "Halvan", "ダグダ": "Dagdar", "タニア": "Tanya", "マーティ": "Marty",
    "ロナン": "Ronan", "リフィス": "Lifis", "サフィ": "Safy", "シヴァ": "Shiva", "アスベル": "Asbel",
    "カリン": "Karin", "フェルグス": "Fergus", "ブライトン": "Brighton", "マチュア": "Machyua", "ラーラ": "Lara",
    "ダルシン": "Dalsin", "ヒックス": "Hicks", "セルフィナ": "Selphina", "ケイン": "Cain", "アルバ": "Alva",
    "ロベルト": "Robert", "グレイド": "Glade", "オルエン": "Olwen", "フレッド": "Fred", "ホメロス": "Homer",
    "シャナム": "Shannam", "パーン": "Perne", "トルード": "Troude", "ティナ": "Tina", "セイラム": "Salem",
    "リノアン": "Linoan", "ディーン": "Dean", "エダ": "Eda", "ラルフ": "Ralf", "イリオス": "Ilios",
    "スルーフ": "Sleuf", "ミーシャ": "Misha", "サラ": "Sara", "ミランダ": "Miranda", "コノモール": "Conomor",
    "ゼーベイア": "Xavier", "アマルダ": "Amalda", "デルムッド": "Diarmuid", "サイアス": "Saias", "セティ": "Ced",
    "ガルザス": "Galzus", "カリオン": "Carrion", "アウグスト": "August", "ドリアス": "Dorias",
    "レイドリック": "Raydrik", "ワイズマン": "Weissman", "バクス": "Bucks", "ゴメス": "Gomez",
    "アイゼナウ": "Eisenau", "アイヒマン": "Eichmann", "ロボス": "Lobos", "マーロック": "Merloch",
    "ラルゴ": "Largo", "オルトフ": "Oltoph", "ケンプフ": "Kempf", "コッダ": "Codha", "コルホ": "Kolkho",
    "バルダック": "Baldack", "ザイル": "Zaille", "ルーメイ": "Rumei", "パウルス": "Paulus", "ブルック": "Brook",
    "ミュラー": "Muller", "ニカラフ": "Nikalaf", "ムーア": "Moore", "コルータ": "Coulter", "グスタフ": "Gustav",
    "ラインコック": "Reincock", "パルマン": "Palman", "ファーデン": "Farden", "ザオム": "Zaom",
    "セイメトル": "Seimetol", "ウォルフ": "Wolf", "マクロイ": "McCloy", "リスト": "List", "アルファン": "Alphand",
    "バラート": "Barath", "コーエン": "Cohen", "フラウス": "Fraus", "ベルド": "Veld", "ラインハルト": "Reinhardt",
    "ハンニバル": "Hannibal", "コープル": "Coirpre", "アルテナ": "Altena", "アリオーン": "Arion",
    "ユリア": "Julia", "セリス": "Seliph", "ユリウス": "Julius", "イシュタル": "Ishtar",
    "キュアン": "Quan", "エスリン": "Ethlyn",
    # named civilians
    "ロミオ": "Romeo", "ユベル": "Hubert", "ルチア": "Lucia", "セイラ": "Sheila", "ピーター": "Peter",
    "ローザ": "Rosa", "エミリ": "Emily", "クリフ": "Cliff", "ベラ": "Bella", "ボーイ": "Boy",
    "マフィー": "Murphy", "リーナ": "Leena",
}

# slug -> (English label, English title).  Titles are plain translations of the Japanese.
CHAPTERS = {
    "opening": ("Opening", ""), "ch01": ("Chapter 1", "The Warrior of Fiana"),
    "ch02": ("Chapter 2", "The Coast of Ith"), "ch02x": ("Chapter 2x", "Pirate Island"),
    "ch03": ("Chapter 3", "The Gate of Kelves"), "ch04": ("Chapter 4", "The Dungeon"),
    "ch04x": ("Chapter 4x", "The Hero of Wind"), "ch05": ("Chapter 5", "Mother and Daughter"),
    "ch06": ("Chapter 6", "Escape"), "ch07": ("Chapter 7", "The Shield of Thracia"),
    "ch08": ("Chapter 8", "Purple Dragon Mountain"), "ch08x": ("Chapter 8x", "Dagdar's Mansion"),
    "ch09": ("Chapter 9", "The Crest of Nova"), "ch10": ("Chapter 10", "Noel Canyon"),
    "ch11": ("Chapter 11", "Fort Dandrum"), "ch11x": ("Chapter 11x", "Murder Holes"),
    "ch12": ("Chapter 12", "The Thieves of Dakia"), "ch12x": ("Chapter 12x", "Dandelion"),
    "ch13": ("Chapter 13", "The Fortress City"), "ch14": ("Chapter 14", "All-Out Attack"),
    "ch14x": ("Chapter 14x", "In Search of Freedom"), "ch15": ("Chapter 15", "Two Roads"),
    "ch16a": ("Chapter 16A", "The Norden Line"), "ch17a": ("Chapter 17A", "Leonster Gate"),
    "ch16b": ("Chapter 16B", "The Dark Forest"), "ch17b": ("Chapter 17B", "May Rain"),
    "ch18": ("Chapter 18", "Liberation of the Capital"), "ch19": ("Chapter 19", "The Empire Strikes Back"),
    "ch20": ("Chapter 20", "The Prince of Light"), "ch21": ("Chapter 21", "The War of Liberation"),
    "ch21x": ("Chapter 21x", "The Prison Camp"), "ch22": ("Chapter 22", "The River Crossing"),
    "ch23": ("Chapter 23", "The Demon King's Castle"), "ch24": ("Chapter 24", "The Baron in Black"),
    "ch24x": ("Chapter 24x", "The Altar of Loptous"), "ch25": ("Final Chapter", "The Sword of Oaths"),
    "ending": ("Ending", ""), "escape": ("Retreat Quotes", ""), "death": ("Death Quotes", ""),
    "shop": ("Shops", ""), "others": ("Miscellaneous", ""),
}

LETTER = {"Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D", "Ｅ": "E", "Ｆ": "F", "Ｇ": "G", "Ｈ": "H"}


def num(s):
    return unicodedata.normalize("NFKC", s)


def chap(s):
    """「１１章外伝」→ Chapter 11x"""
    s = num(s)
    return "Chapter " + s.replace("章外伝", "x").replace("章", "")


class Unknown(Exception):
    pass


def N(name):
    if name not in NAMES:
        raise Unknown(name)
    return NAMES[name]


TITLES = {
    "オープニング": "Opening", "ナレーション": "Narration", "民家": "House", "教会": "Church",
    "僧院": "Monastery", "闘技場": "Arena", "武器屋・道具屋": "Armory / Item shop",
    "制圧後": "After seizing", "制圧時": "On seizing", "スタッフロール": "Staff roll",
    "門に隣接": "Next to the gate", "リーフ離脱後": "After Leif escapes", "リーフ離脱時": "When Leif escapes",
    "ナンナ離脱時": "When Nanna escapes",
    "そして、最後はいつもの…": "And finally, the usual…",
    "ターン数と総合評価の表示": "Turn counts and overall ranking",
    "前景色：黒、背景色：白の画面": "Screen with black text on a white background",
    "アルスター軍を１体でも倒した直後": "Right after defeating any Ulster unit",
    "エーヴェルが捕虜となったとき": "When Eyvel is captured",
    "オルエン→ケンプフの会話直後の敵フェーズ": "Enemy phase right after Talk: Olwen → Kempf",
    "オーシンとハルヴァンの練習シーン": "Osian and Halvan's training scene",
    "ケンプフ初戦後の敵ターン": "Enemy turn after first fighting Kempf",
    "セイラム→サラ（敵の場合のみ）の会話": "Talk: Salem → Sara (only while she is an enemy)",
    "リーフ（リフィス）→ダルシンの会話": "Talk: Leif (or Lifis) → Dalsin",
    "セティが死亡したとき": "When Ced dies",
    "ハンニバル出撃後の敵フェーズ": "Enemy phase after Hannibal sorties",
    "ホメロスのいる民家": "House where Homer is",
    "ポートクリス作戦発動直後": "Right after the 'Port Chris' operation begins",
    "マリータが捕獲・死亡したとき、闘技場の扉を開けたときの続き":
        "If Mareeta was captured or killed: continuation of 'When the arena door is opened'",
    "マリータ登場から２ターン後の敵フェーズ": "Enemy phase two turns after Mareeta appears",
    "マンスター軍が１体でも残っていて、リーフ軍の誰かが離脱したとき":
        "When someone in Leif's army escapes while any Munster unit remains",
    "ラルフが仲間になった直後のＮＰＣフェイズ": "NPC phase right after Ralf joins",
    "リノアンが捕獲・死亡した章をクリアしたときの追加メッセージ":
        "Extra message on clearing a chapter in which Linoan was captured or killed",
    "リフィスのいる牢屋の扉が空いたとき": "When the door to Lifis's cell is opened",
    "リーフのいる牢屋の扉が空いたとき": "When the door to Leif's cell is opened",
    "リーフが中央の部屋に侵入したとき": "When Leif enters the central room",
    "リーフが右の離脱ポイントに到着したとき": "When Leif reaches the right escape point",
    "リーフが左の離脱ポイントに到着したとき": "When Leif reaches the left escape point",
    "リーフ死亡時の追加メッセージ": "Extra message when Leif dies",
    "リーフ軍がサイアスを中心とした５×５範囲内に侵入したことがあるとき":
        "If Leif's army has entered the 5×5 area centred on Saias",
    "リーフ軍が城に接近して待機した直後の敵フェーズ１":
        "Enemy phase right after Leif's army waits near the castle (1)",
    "リーフ軍が城に接近して待機した直後の敵フェーズ２":
        "Enemy phase right after Leif's army waits near the castle (2)",
    "リーフ軍が城付近に近づいたとき": "When Leif's army approaches the castle",
    "リーフ軍が城壁内に侵入": "Leif's army enters the castle walls",
    "リーフ軍フェーズ開始時、すべての魔法陣にリーフ軍が待機しているとき":
        "At the start of Leif's phase, with his units waiting on every magic circle",
    "剣闘士を１人倒すか、リーフ軍が闘技場への扉近くまで接近したとき":
        "When a gladiator is defeated or Leif's army nears the arena door",
    "城下の南門の上に待機したとき": "When a unit waits on the town's south gate",
    "子供が、キアの杖のある部屋の扉の前に立ったとき":
        "When a child stands before the door of the room holding the Kia Staff",
    "山荘が敵に制圧されたとき": "When the enemy seizes the mountain villa",
    "市民のいる牢屋の扉（上）を開けたとき": "When the civilians' cell door (top) is opened",
    "市民のいる牢屋の扉（下）を開けたとき": "When the civilians' cell door (bottom) is opened",
    "市民のいる牢屋の扉（右）が空いたとき": "When the civilians' cell door (right) is opened",
    "市民のいる牢屋の扉（左）が空いたとき": "When the civilians' cell door (left) is opened",
    "敵にターラを制圧されてしまったとき": "When the enemy seizes Tahra",
    "敵４ターン目、もしくはエリア進入": "Enemy turn 4, or on entering the area",
    "玉座が敵に制圧されてしまったとき": "When the enemy seizes the throne",
    "闘技場の扉が開く前に、ナンナが生存していて、エーヴェルが石化しているとき":
        "Before the arena door opens, if Nanna is alive and Eyvel has been petrified",
    "闘技場の扉を開けたとき": "When the arena door is opened",
    "１５ターン目以降、バラートを打倒したとき": "When Barath is defeated on turn 15 or later",
}

SUBS = {
    "いじめられっ子といじめっ子": "The bullied and the bully",
    "おかえり、ハンニバル": "Welcome back, Hannibal",
    "かわいいユリア様と、よそみのセリス様": "Adorable Lady Julia and a distracted Lord Seliph",
    "さらに急ぐリーフたち": "Leif's group hurries on",
    "はじめての夜戦": "The first night battle",
    "アウグストとの再会": "Reunion with August",
    "アウグストの策謀": "August's scheme",
    "アスベル登場！": "Enter Asbel!",
    "アルバイター・ルーメイ": "Rumei the part-timer",
    "オルエンお嬢様": "Young Lady Olwen",
    "オルエン様、初登場！": "Lady Olwen's first appearance!",
    "カリンとフェルグスの出会い": "Karin and Fergus meet",
    "ガルザスの追跡": "Galzus's pursuit",
    "ケンプフの罠": "Kempf's trap",
    "サフィのいけない心配！？": "Safy's improper worries!?",
    "シヴァの策謀": "Shiva's scheme",
    "セティ様ぁ～！": "Lord Ceeed~!",
    "ナンナとマリータを追ってマンスターへ": "To Munster, after Nanna and Mareeta",
    "ハンニバルの心遣い": "Hannibal's consideration",
    "フィアナで育った少年・リーフ": "Leif, the boy raised in Fiana",
    "フリージ第２０軍団の策謀": "The scheme of Friege's 20th Corps",
    "ヘッドハンター・カリン": "Karin the headhunter",
    "ベルド登場！": "Enter Veld!",
    "マギ団の策謀": "The Magi Squad's scheme",
    "ユリウスとイシュタル！": "Julius and Ishtar!",
    "リフィスの本性": "Lifis's true nature",
    "リフィスの策謀": "Lifis's scheme",
    "ルーメイ出撃": "Rumei sorties",
    "レイドリックの策謀": "Raydrik's scheme",
    "レンスター奪還を夢に": "Dreaming of retaking Leonster",
    "南トラキアの現状を知った、リーフ": "Leif learns the state of southern Thracia",
    "囚われのリーフ王子": "Prince Leif, captive",
    "娘たち、中年男に誘拐される！": "The girls are kidnapped by a middle-aged man!",
    "子供狩り": "The child hunts",
    "怯えるレイドリック": "A frightened Raydrik",
    "感動のエンディング…の一歩手前…": "One step before… the moving ending…",
    "捕獲されたまま、マップ外に連れ去られた場合も含む": "Includes being carried off the map while captured",
    "教えてっ、ドリアス！": "Teach us, Dorias!",
    "村が危ない！": "The village is in danger!",
    "現実のゴメス": "Gomez, in reality",
    "現実を知る王子": "The prince learns the reality",
    "白馬…から降りた…王子様じゃなくて、副官登場":
        "Off his white horse… not a prince, but an adjutant appears",
    "絵の表示は総合ランクＡ以上のもの": "Illustrations are shown at overall rank A or higher",
    "親分登場！": "Enter the boss!",
    "追跡するマンスター軍": "The Munster army gives chase",
    "逃げるリーフ軍": "Leif's army flees",
    "進軍！ランスリッター": "Advance! Lanzenritter",
    # positions
    "一番上": "topmost", "上": "top", "上方の右": "upper area, right", "上方の左": "upper area, left",
    "下": "bottom", "中央": "centre", "中央上": "centre top", "中央下": "centre bottom",
    "中央右": "centre right", "中央州": "central sandbank", "中央左": "centre left",
    "中央左下": "centre lower left", "北": "north", "南": "south",
    "南門の右": "right of the south gate", "南門の左": "left of the south gate",
    "右": "right", "右上": "upper right", "右下": "lower right", "左": "left", "左上": "upper left",
    "左下": "lower left", "左下以外": "all except lower left", "左から２番目": "2nd from the left",
    "左方の右": "left area, right", "左方の左": "left area, left", "左端": "far left", "最も左": "leftmost",
}

CONDS = {
    "「いいえ」を選んだか、Ｂボタンでキャンセルした場合": "If 「いいえ」 (No) is chosen or cancelled with the B button",
    "「はい」を選んだ場合": "If 「はい」 (Yes) is chosen",
    "「はい」を選択した場合": "If 「はい」 (Yes) is chosen",
    "「売る」を選んだ場合": "If 「売る」 (Sell) is chosen",
    "「買う」もしくは「売る」を選んだ場合": "If 「買う」 (Buy) or 「売る」 (Sell) is chosen",
    "「買う」を選んだ場合": "If 「買う」 (Buy) is chosen",
    "お金が足りない場合": "If you don't have enough gold",
    "お金が足りる場合": "If you have enough gold",
    "これまでの章で、ひとりも捕虜にされていない場合": "If no one has been taken prisoner in earlier chapters",
    "これまでの章で、誰かひとりでも捕虜にされている場合": "If anyone has been taken prisoner in earlier chapters",
    "すでにリーフ→オルエンの会話をしている場合": "If Talk: Leif → Olwen has already happened",
    "すでにリーフ→グレイドの会話をしていた場合": "If Talk: Leif → Glade has already happened",
    "まだ、リーフ→グレイドの会話をしていない場合": "If Talk: Leif → Glade has not happened yet",
    "まだリーフ→オルエンの会話をしていない場合": "If Talk: Leif → Olwen has not happened yet",
    "すべての民家が破壊されていない場合": "If no houses have been destroyed",
    "どこか１つでも民家が破壊されている場合": "If any house has been destroyed",
    "まだアイテムを１つでも持っている場合のみ": "Only if the unit still has at least one item",
    "アイテムを１つでも持っている場合": "If the unit has at least one item",
    "アイテムを１つも持っていない場合": "If the unit has no items",
    "アイテム欄に空きがある場合": "If there is room in the inventory",
    "アイテム欄に空きがない場合": "If the inventory is full",
    "エーヴェル、ナンナがともに生存": "Eyvel and Nanna both alive",
    "エーヴェルがいなくて、フィンがいる場合": "If Eyvel is absent and Finn is present",
    "エーヴェルがいる場合": "If Eyvel is present",
    "エーヴェルもフィンもいない場合": "If neither Eyvel nor Finn is present",
    "エーヴェルがリーフ軍にいて、生存しているとき": "If Eyvel is in Leif's army and alive",
    "ナンナがリーフ軍にいて、生存しているとき": "If Nanna is in Leif's army and alive",
    "フィンがリーフ軍にいて、生存しているとき": "If Finn is in Leif's army and alive",
    "エーヴェルが捕獲されていない場合": "If Eyvel has not been captured",
    "エーヴェルが捕獲されている場合": "If Eyvel has been captured",
    "エーヴェルが生存、ナンナが捕獲されているとき": "If Eyvel is alive and Nanna has been captured",
    "エーヴェルが生存、ナンナが死亡しているとき": "If Eyvel is alive and Nanna is dead",
    "エーヴェルが石化、ナンナが死亡・捕獲されているとき": "If Eyvel is petrified and Nanna is dead or captured",
    "エーヴェルが石化、ナンナが生存しているとき": "If Eyvel is petrified and Nanna is alive",
    "オルエンがリーフ軍に加わっていて、かつ生存している場合のみ": "Only if Olwen has joined Leif's army and is alive",
    "オルエンがリーフ軍に加わっていて、生存している場合のみ": "Only if Olwen has joined Leif's army and is alive",
    "オルエンが出撃している場合のみ": "Only if Olwen is deployed",
    "カリン→ミーシャの会話をしていて、かつミーシャを捕獲したまま制圧した場合":
        "If Talk: Karin → Misha happened and you seize while holding Misha captive",
    "コノモールを離脱させている場合": "If Conomor has been made to retreat",
    "コーエン死亡・捕虜時": "If Cohen is dead or a prisoner",
    "サイアス離脱前": "Before Saias leaves", "サイアス離脱後": "After Saias leaves",
    "サラが死亡・捕獲されているか、キアの杖を入手していないとき":
        "If Sara is dead or captured, or you do not have the Kia Staff",
    "サラが生存していて、キアの杖を入手しているとき": "If Sara is alive and you have the Kia Staff",
    "セティを仲間にしていないとき": "If Ced has not been recruited",
    "セティを仲間にしているとき": "If Ced has been recruited",
    "タニアが死亡・捕獲されていて、ダグダが生存しているとき": "If Tanya is dead or captured and Dagdar is alive",
    "ダグダが死亡・捕獲されていて、タニアが生存しているとき": "If Dagdar is dead or captured and Tanya is alive",
    "フィンが死亡・捕獲されていて、サフィが生存しているとき": "If Finn is dead or captured and Safy is alive",
    "トルードが捕獲・死亡していない場合のみ": "Only if Troude has not been captured or killed",
    "トルードを捕獲したまま制圧した場合のみ": "Only if you seize while holding Troude captive",
    "ルーメイを捕獲したまま制圧した場合のみ": "Only if you seize while holding Rumei captive",
    "１２章でセイラムを捕獲したまま制圧した場合のみ": "Only if you seized Chapter 12 while holding Salem captive",
    "ナンナが死亡・捕獲されている場合のみ": "Only if Nanna is dead or captured",
    "ナンナが生存している場合のみ": "Only if Nanna is alive",
    "フィンが生存している場合のみ": "Only if Finn is alive",
    "ナンナ以外の女性キャラで訪れた場合": "If a female character other than Nanna visits",
    "ナンナ死亡時": "If Nanna is dead",
    "ニカラフが死亡・捕獲されている場合": "If Nikalaf is dead or captured",
    "ニカラフが生存している場合": "If Nikalaf is alive",
    "フェルグスとカリンがともに生存している場合のみ": "Only if Fergus and Karin are both alive",
    "フレッドが死亡しているか、３１ターン以上経過しているとき": "If Fred is dead or 31 or more turns have passed",
    "フレッドが生存していて、３０ターン以内のとき": "If Fred is alive and it is within 30 turns",
    "ブラギの剣を手に入れていない場合": "If you have not obtained the Bragi Sword",
    "ブラギの剣を手に入れている場合": "If you have obtained the Bragi Sword",
    "ミランダを仲間にしていて、かつ生存している場合": "If Miranda has been recruited and is alive",
    "ミランダを仲間にしていない、もしくは生存していない場合": "If Miranda has not been recruited or is not alive",
    "ミランダ生存時のみ（森ルートを進軍してきた場合のみ）": "Only if Miranda is alive (forest route only)",
    "ラルゴ将軍を打倒・解放して制圧した場合": "If you seize after defeating or releasing General Largo",
    "ラルゴ将軍を捕虜にしたまま制圧した場合": "If you seize while holding General Largo prisoner",
    "ラーラを出撃させた場合のみ": "Only if Lara is deployed",
    "リフィスを出撃させた場合のみ": "Only if Lifis is deployed",
    "リフィスを出撃させている場合のみ": "Only if Lifis is deployed",
    "リフィスを捕獲している場合のみ": "Only if Lifis has been captured",
    "レジスタンス部隊に助けを求めていないか、誰も死んでいない場合のみ":
        "Only if you did not ask the resistance for help, or none of them died",
    "レンスター軍を１人も倒さなかった場合（捕獲・解放は影響なし）":
        "If you defeated no Leonster soldiers (capturing and releasing does not count)",
    "何かアイテムを選んだ場合": "If an item is selected",
    "何か商品を選んだ場合": "If a product is selected",
    "先にリーフ→セルフィナの会話シーンを見ていた場合のみ": "Only if Talk: Leif → Selphina was seen first",
    "売れないアイテムの場合": "If the item cannot be sold",
    "売れるアイテムの場合": "If the item can be sold",
    "子供キャラで訪れた場合": "If a child character visits",
    "男性キャラで訪れた場合": "If a male character visits",
    "市民を全員離脱させた場合のみ": "Only if every civilian escaped",
    "武器屋の場合": "At an armory", "道具屋の場合": "At an item shop",
    "民家（左下）で２００００Ｇ払っている場合のみ": "Only if you paid 20000G at the house (lower left)",
    "試合に勝った場合": "If you win the match", "試合に負けた場合": "If you lose the match",
    "試合途中でＢボタンを押してキャンセルした場合": "If you cancel mid-match with the B button",
    "Ｂボタンでキャンセルした場合": "If cancelled with the B button",
    "１０～１８章の場合（リーフの指揮レベルが２のとき）": "In Chapters 10–18 (when Leif's leadership is 2)",
    "２章外伝、もしくは６章以降の場合（リーフの指揮レベルが１以上のとき）":
        "In Chapter 2x, or Chapter 6 onward (when Leif's leadership is 1 or more)",
    "１１章外伝でローザを離脱させていてオルエンで訪れたとき":
        "If Rosa escaped in Chapter 11x and Olwen visits",
    "１１章外伝でローザを離脱させていてオルエン以外で訪れたとき、もしくは１１章外伝に行っていないとき":
        "If Rosa escaped in Chapter 11x and someone other than Olwen visits, or you skipped Chapter 11x",
    "１３ラウンド目までに勝敗が決まらなかった場合": "If the match is undecided by round 13",
    "１６章Ａでコノモールを倒していない場合のみ": "Only if you did not defeat Conomor in Chapter 16A",
    "１７章Ｂでアマルダを倒していない場合のみ": "Only if you did not defeat Amalda in Chapter 17B",
    "２章外伝でシヴァを倒さなかった場合のみ": "Only if you did not defeat Shiva in Chapter 2x",
    "１９ターン以内のとき": "Within 19 turns", "２０ターン以降のとき": "On turn 20 or later",
    "２００００Ｇ以上持っている場合": "If you have 20000G or more",
    "２００００Ｇ未満しか持っていない場合": "If you have less than 20000G",
    "２３章でどちらも仲間にしなかった場合（サイアス捕獲・死亡時）":
        "If you recruited neither in Chapter 23 (Saias captured or dead)",
    "２３章でサイアスを仲間にした場合": "If you recruited Saias in Chapter 23",
    "２３章でセティを仲間にした場合": "If you recruited Ced in Chapter 23",
    "３章でコープルを民家まで送りとどけていた場合のみ": "Only if you delivered Coirpre to the house in Chapter 3",
    "３章までオーシン、ハルヴァン、ロナンの誰かひとりでも生存していた場合のみ":
        "Only if any of Osian, Halvan or Ronan survived through Chapter 3",
    "４章外伝でリーナを救出していないとき": "If you did not rescue Leena in Chapter 4x",
    "４章外伝に行っていない場合のみ": "Only if you skipped Chapter 4x",
    "４章外伝に行っていなくて、まだ５ターン以内のとき": "If you skipped Chapter 4x and it is within 5 turns",
    "５、６章でガルザスを打倒・解放した場合": "If you defeated or released Galzus in Chapters 5–6",
    "５、６章でガルザスを打倒・解放（捕獲のみは除く）していない場合":
        "If you did not defeat or release Galzus in Chapters 5–6 (capture alone does not count)",
}

DIRS = {
    "☆処理始点へ戻る": "Return to ☆ start of menu", "☆売却処理始点へ戻る": "Return to ☆ start of selling",
    "☆購入処理始点へ戻る": "Return to ☆ start of buying",
    "この場合、民家の門は閉じないので何度でも訪問できる":
        "In this case the house's gate does not close, so it can be visited repeatedly",
    "アイテムの売却がキャンセルされる": "The sale is cancelled",
    "アイテムの選択画面へ": "To the item selection screen", "アイテムを売却": "Item is sold",
    "アリオーンがターラ城にやってくる": "Arion arrives at Tahra castle",
    "アルテナが現れる": "Altena appears",
    "ウォルフの体格が２０で捕獲できないので、確認できず": "Wolf's build is 20, so he cannot be captured; unverified",
    "オルエンが奥に連れて行かれる": "Olwen is taken into the back",
    "カリオン登場": "Carrion appears", "サイアスが配置につく": "Saias takes his position",
    "シーンがマップ上に移る": "The scene moves to the map",
    "ナンナのウィンドウが閉じる": "Nanna's window closes",
    "パウルスが去っていく": "Paulus leaves",
    "フレッドがケンプフの目前にやってくる": "Fred comes up in front of Kempf",
    "マリータが死亡し、マップ上から消える": "Mareeta dies and vanishes from the map",
    "マリータとサイアスがワープして消える": "Mareeta and Saias warp away",
    "ラインハルトがマップ右側へ去ってゆく": "Reinhardt leaves toward the right of the map",
    "ラインハルトがマップ左側から、バラートの右上までやってくる":
        "Reinhardt comes from the left of the map to the upper right of Barath",
    "レストの杖入手": "Restore staff obtained", "会話なし": "No dialogue",
    "剣闘士たちが登場する": "The gladiators appear",
    "右側に『アリオーン、アルテナ』の絵が表示される": "An illustration of Arion and Altena appears on the right",
    "右側に『アルテナ（ノヴァ？）』の絵が表示される": "An illustration of Altena (Nova?) appears on the right",
    "右側に『キュアン、フィン、グレイド、セルフィナ』の絵が表示される":
        "An illustration of Quan, Finn, Glade and Selphina appears on the right",
    "右側に『キュアンがエスリンに乗馬を教えているところ』の絵が表示される":
        "An illustration of Quan teaching Ethlyn to ride appears on the right",
    "右側に『キュアン一家』の絵が表示される": "An illustration of Quan's family appears on the right",
    "商品の購入がキャンセルされる": "The purchase is cancelled",
    "商品の選択画面へ": "To the product selection screen", "商品を購入": "Product is bought",
    "戦闘シーンへ": "To the battle scene", "扉が開く": "The door opens",
    "捕獲不可能": "Cannot be captured", "流星剣発動！": "Astra activates!",
    "章のタイトル": "chapter title", "１３年後": "13 years later",
    "→5のとき": "→ in Chapter 5", "→5のみ": "→ Chapter 5 only",
    "→このあと、会話発生": "→ a conversation follows",
    "上": "top",
}

MARKS = {"☆処理始点": "☆ Start of menu", "☆売却処理始点": "☆ Start of selling", "☆購入処理始点": "☆ Start of buying"}


def title(t):
    t = t.strip().strip("　")
    if t in TITLES:
        return TITLES[t]
    m = re.fullmatch(r"(.+?)(初戦時|打倒時|解放時|捕獲時)", t)
    if m:
        what = {"初戦時": "battle quote", "打倒時": "defeat quote",
                "解放時": "release quote", "捕獲時": "capture quote"}[m.group(2)]
        return f"{N(m.group(1))}: {what}"
    m = re.fullmatch(r"(.+?)の後日談", t)
    if m:
        return f"{N(m.group(1))}: epilogue"
    m = re.fullmatch(r"(.+?)(→|⇔)(.+?)の会話", t)
    if m:
        arrow = "→" if m.group(2) == "→" else "↔"
        return f"Talk: {N(m.group(1))} {arrow} {N(m.group(3))}"
    m = re.fullmatch(r"(敵|ＮＰＣ)?([０-９]+)ターン目([０-９]?)", t)
    if m:
        who = {"敵": "Enemy turn", "ＮＰＣ": "NPC turn", None: "Turn"}[m.group(1)]
        part = f" ({num(m.group(3))})" if m.group(3) else ""
        return f"{who} {num(m.group(2))}{part}"
    for jp, en in (("オープニング", "Opening {}"), ("制圧後", "After seizing ({})"), ("シーン", "Scene {}")):
        m = re.fullmatch(jp + r"([０-９]+)", t)
        if m:
            return en.format(num(m.group(1)))
    for jp, en in (("家族の説得", "Persuaded by family ({})"), ("残念な後日談", "Unhappy epilogue ({})"),
                   ("シビリアン離脱時", "When a civilian escapes ({})")):
        m = re.fullmatch(jp + r"([Ａ-Ｈ])", t)
        if m:
            return en.format(LETTER[m.group(1)])
    raise Unknown(t)


def sub(t):
    if t in SUBS:
        return SUBS[t]
    m = re.fullmatch(r"(右|左)(側の上|方の左)から([０-９]+)番目", t)
    if m:
        n = num(m.group(3))
        nth = n + {"1": "st", "2": "nd", "3": "rd"}.get(n, "th")
        side = "right" if m.group(1) == "右" else "left"
        if m.group(2) == "側の上":
            return f"{side} side, {nth} from the top"
        return f"{side} area, {nth} from the left"
    raise Unknown(t)


def cond(t):
    t = t.lstrip("※")
    if t in CONDS:
        return CONDS[t]
    m = re.fullmatch(r"([０-９]+)章まで(.+?)生存時のみ", t)
    if m:
        return f"Only if {N(m.group(2))} survived through Chapter {num(m.group(1))}"
    m = re.fullmatch(r"(.+?)を担いで訪問(した|しなかった)場合", t)
    if m:
        return f"If the visitor is {'' if m.group(2) == 'した' else 'not '}carrying {N(m.group(1))}"
    m = re.fullmatch(r"(.+?)生存時(のみ)?", t)
    if m:
        return ("Only if " if m.group(2) else "If ") + f"{N(m.group(1))} is alive"
    m = re.fullmatch(r"(.+?)(以外)?で訪(?:れ|問し)た(?:場合|とき)", t)
    if m:
        who = N(m.group(1))
        return f"If someone other than {who} visits" if m.group(2) else f"If {who} visits"
    m = re.fullmatch(r"([０-９]+章外伝)で(.+?)を離脱させて(いる|いない)場合(?:のみ)?", t)
    if m:
        did = "escaped" if m.group(3) == "いる" else "did not escape"
        return f"If {N(m.group(2))} {did} in {chap(m.group(1))}"
    raise Unknown(t)


def direction(t):
    inner = t.strip()
    if inner.startswith("（") and inner.endswith("）"):
        inner = inner[1:-1]
    if inner in DIRS:
        return f"({DIRS[inner]})"
    raise Unknown(t)


def mark(t):
    if t in MARKS:
        return MARKS[t]
    m = re.fullmatch(r"(.+)（登場章：(.+)）", t, re.S)   # built by build.py for the quote tables
    if m:
        chaps = " / ".join(num(c).replace("外", "x") for c in m.group(2).split())
        return f"{m.group(1)} — appears in Chapter {chaps}"
    raise Unknown(t)
