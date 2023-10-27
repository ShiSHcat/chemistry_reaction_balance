import Discord, { Client, IntentsBitField } from 'discord.js';
import { REST } from '@discordjs/rest';
import { Routes } from 'discord-api-types/v9';
import { balanceReaction } from './balance_api_calls.js';
import {tid, token} from "./token.js"
//COMMANDS
const commands = [
    {
        name: 'bilancia',
        description: 'Bilancia una reazione chimica',
        options: [
            {
                name: 'reazione',
                description: 'Reazione da bilanciare',
                type: 3,
                required: true,
            },
            {
                name: 'log',
                description: 'Se vuoi avere il log della bilanciatura',
                type: 5,
                required: false,
            }
        ]
    },
];

//SET COMMANDS
const rest = new REST({ version: '9' }).setToken(token);
(async () => {
    try {
        console.log('Started refreshing application (/) commands.');

        await rest.put(Routes.applicationCommands(tid), { body: commands });

        console.log('Successfully reloaded application (/) commands.');
    } catch (error) {
        console.error(error);
    }
})();

//BUSINESS LOGIC
const client = new Client({ intents: [IntentsBitField.Flags.Guilds] });
client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});
client.on('interactionCreate', async (interaction) => {
    if (!interaction.isCommand()) return;
    if (interaction.commandName === 'bilancia') {
        let reazione = interaction.options.getString('reazione');
        let log = interaction.options.getBoolean('log');
        if(!log) log = true;
        let result = await balanceReaction(reazione);
        if(!result.ok) return interaction.reply(result.log);
        if(result.reaction) return interaction.reply(
            "Reazione iniziale: ```"+
            reazione+
            "```\n"+
            result.log+
            "\n```"+
            result.reaction+"```"
        );
    }
});
//LOGIN
client.login(token)