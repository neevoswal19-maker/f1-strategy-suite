#> # 1. Setup
#> ### 1.1 Your choices
#> Fill in the form, then use **Runtime → Run all**.
#> - **SEASON**: any season from 2019 onwards.
#> - **RACE**: round number or Grand Prix name (`5`, `Monaco`, `Silverstone`). Leave it blank for the next race of that season (or its last race if the season is over).
#> - **DRIVER**: three-letter code (`VER`, `NOR`, `LEC`) whose pit strategy is simulated. Leave it blank to use the race winner.
#> - **SAVE_CACHE_TO_DRIVE**: keep downloaded data in Google Drive so it survives a Colab restart (Colab will ask for Drive access).
#@title Race, driver and cache { display-mode: "form" }
SEASON = 2026  #@param {type:"integer"}
RACE = ""  #@param {type:"string"}
DRIVER = ""  #@param {type:"string"}
SAVE_CACHE_TO_DRIVE = False  #@param {type:"boolean"}
