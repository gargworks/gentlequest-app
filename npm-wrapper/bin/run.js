#!/usr/bin/env node

const { spawnSync } = require('child_process');
const sys = require('sys');

const args = process.argv.slice(2);

function runCommand(command, args) {
    const result = spawnSync(command, args, { stdio: 'inherit', shell: true });
    if (result.error) {
        return false;
    }
    return result.status === 0;
}

// 1. Try running directly
const success = runCommand('nucleus-mcp', args);

if (!success) {
    console.log('Nucleus-MCP not found. Attempting to install via pip...');
    const installSuccess = runCommand('pip', ['install', 'nucleus-mcp']);

    if (installSuccess) {
        console.log('Successfully installed nucleus-mcp. Running command...');
        runCommand('nucleus-mcp', args);
    } else {
        console.error('Failed to install nucleus-mcp. Please ensure python3 and pip are installed.');
        process.exit(1);
    }
}
