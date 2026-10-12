This exchange bot allows you to see the prices of assets, and it's not just an application that displays prices; The `/track` command, which also allows you to track the stock market, sends you notifications via Telegram for every 0.05% price change of the assets you add to your watchlist. Additionally, the `/guess` command compares the price changes of an asset over the last 20 days and the last 5 days, predicting whether the asset will rise or fall (these predictions are for informational purposes only and are not investment advice!).

All commands:

'/padd' = Add amount to portfolio

'/pset' = Set exact amount in portfolio

'/pdel' = Remove asset from portfolio

'/portfolio' = Show portfolio with live values

`/exchanges` = lists all assets loaded into the bot

`/track` = adds an asset to your watchlist

`/untrack` = removes an asset from your watchlist

`/list` = shows your watchlist

`/guess` = predicts whether the asset will rise or fall (not investment advice!)

`/commands` = shows all commands loaded into the bot


To see the price of an asset, type its name in the `/exchanges` list.

Technologies used:

`PostgresSQL (Neon DB):` We used PostgreSQL to store and manage user watchlists when deploying the bot, and Neon DB as the database.

'UptimeRobot:' To keep the bot open

`Telegram:` The bot is a Telegram bot

'Python:' The bot was written using Python.

'Render:' To deploy the bot

'Yahoo Finance:' All asset prices were retrieved using Yahoo Finance.
