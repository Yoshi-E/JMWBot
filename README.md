# JMWBot

## Monetization
This Bot (or code that I own inside) __cannot__ be used in a monetization process.

## Licence

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" property="dct:title">BECTI Zerty Edit.</span> by <span xmlns:cc="http://creativecommons.org/ns#" property="cc:attributionName">Zerty</span> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.<br />Based on a work at <a xmlns:dct="http://purl.org/dc/terms/" href="http://forums.bistudio.com/showthread.php?166433-SP-MP-BeCTI" rel="dct:source">http://forums.bistudio.com/showthread.php?166433-SP-MP-BeCTI</a>.

This project is not affiliated or authorized by Discord or Bohemia Interactive a.s. Bohemia Interactive, ARMA, DAYZ and all associated logos and designs are trademarks or registered trademarks of Bohemia Interactive a.s. 

## Credits:
- 


## Examples

You can use this bot to analyse the performance of your mission on your server.
![advanced_1](https://github.com/Yoshi-E/jmwBOT/blob/dev/examples/2018-10-27_3-32-27562-ADV.png)
Or use it to look at the current balance of the game in a detailed graph.
![advanced_2](https://github.com/Yoshi-E/jmwBOT/blob/dev/examples/2018-10-27_22-22-34235-CUR-ADV.png)
Promoting the mission with it as a summary is also possible
![advanced_3](https://github.com/Yoshi-E/jmwBOT/blob/dev/examples/discord_usage_example.PNG)


## Usage

This discord bot is designed with flexablity in mind. The core pricinple for it is to listen to a game log and to react and summarize events in the given log. This can be any kind of game that logs details of events to a text file. In theory this bot should work with other game such as CSGO, Minecraft, GTA, ... and many more.

In the current version the bot listens to 3 types of log entries:

* CTI_Mission_Performance: Starting Server
* CTI_Mission_Performance: GameOver
* ["CTI_Mission_Performance:",["time",110.087],["fps",49.2308],["score_east",0], ...

This helps the bot to understand the current state of the game, and helps it to report game starts and ends, and as well to create a summary of its performance.
