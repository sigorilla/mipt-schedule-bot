# MIPT Schedule Bot
Telegram Bot for MIPT students. They can know current schedule for they group.

## Commands

* `/start` - begins interaction with the user.
* `/help` - returns a help message.
* `/settings` - returns the bot's settings for this user and suggests commands to set default group.
   * `[number]` - set `number` as default user's group.
   * `/cancel` - cancel set of default user's group. 
* `/group [number]` - return schedule for `number` group.
* `/today` - return schedule to user's group.
