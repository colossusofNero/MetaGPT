require('dotenv').config();
const axios = require('axios');
const fs = require('fs');
const { execSync } = require('child_process');

// Load API keys securely
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;  // Updated to match GitHub Secrets
const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
const GITHUB_TOKEN = process.env.GIT_TOKEN;

// Load AI task definitions
const tasks = JSON.parse(fs.readFileSync('tasks.json', 'utf8'));

// Function to call OpenAI (ChatGPT)
async function callAI(apiKey, model, prompt) {
    try {
        console.log(`🔍 Calling OpenAI (${model})...`);
        const response = await axios.post(
            "https://api.openai.com/v1/chat/completions",
            {
                model: model,
                messages: [
                    { role: "system", content: "You are a helpful AI coding assistant." },
                    { role: "user", content: prompt }
                ],
                max_tokens: 1000
            },
            {
                headers: {
                    "Authorization": `Bearer ${apiKey}`,
                    "Content-Type": "application/json"
                }
            }
        );
        return response.data.choices[0].message.content.trim();
    } catch (error) {
        console.error(`❌ Error calling OpenAI (${model}):`, error.response ? error.response.data : error.message);
        return null;  // Prevents crashes when API fails
    }
}

// Function to call Anthropic (Claude)
async function callClaudeAI(apiKey, prompt) {
    try {
        console.log("🔍 Calling Claude AI...");
        const response = await axios.post(
            "https://api.anthropic.com/v1/messages",
            {
                model: "claude-2",
                max_tokens: 1000,
                messages: [{ role: "user", content: prompt }]
            },
            {
                headers: {
                    "x-api-key": apiKey,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
            }
        );
        return response.data.content[0].text.trim();
    } catch (error) {
        console.error(`❌ Error calling Claude API:`, error.response ? error.response.data : error.message);
        return null;
    }
}

// Generate AI-generated code
async function generateCode() {
    console.log("🔍 Requesting AI-generated code...");

    // Backend (ChatGPT)
    const backendPrompt = `
    Write a well-structured Node.js backend using Express.js for the following feature: "${tasks.backend}". 
    Follow these guidelines:
    - Use Express.js for routing
    - Implement proper error handling (try/catch)
    - Use environment variables for configurations (dotenv)
    - Organize code into a structured format (controllers, routes, services)
    - Include comments explaining each function
    - Return JSON responses with appropriate HTTP status codes

    Provide ONLY the JavaScript code. Do not include explanations.
    `;
    const backendCode = await callAI(OPENAI_API_KEY, "gpt-4-turbo", backendPrompt);
    
    if (backendCode) {
        fs.writeFileSync('src/backend.js', backendCode);
        console.log("✅ Backend code generated.");
    } else {
        console.log("❌ Backend code generation failed.");
    }

    // Frontend (Claude)
    const frontendPrompt = `
    Write a well-structured React component for the following feature: "${tasks.frontend}". 
    Follow these guidelines:
    - Use functional components with hooks (React.useState, React.useEffect)
    - Use Tailwind CSS for styling (or inline styles if preferred)
    - Implement proper form validation using React Hook Form or simple state validation
    - Ensure accessibility (ARIA attributes where necessary)
    - Export the component properly

    Provide ONLY the React code. Do not include explanations.
    `;
    const frontendCode = await callClaudeAI(CLAUDE_API_KEY, frontendPrompt);
    
    if (frontendCode) {
        fs.writeFileSync('src/frontend.js', frontendCode);
        console.log("✅ Frontend code generated.");
    } else {
        console.log("❌ Frontend code generation failed.");
    }
}

// Commit AI-generated code to GitHub
async function commitCode() {
    console.log("📂 Committing AI-generated code...");
    try {
        execSync('git add src/backend.js src/frontend.js');
        execSync('git commit -m "Added AI-generated backend and frontend"');
        execSync('git push origin main');
        console.log("🚀 Code successfully pushed to GitHub!");
    } catch (error) {
        console.error("❌ Git push failed:", error.message);
    }
}

// 🚀 Run AI Code Generation & Commit Process
async function runMetaGPT() {
    await generateCode();
    await commitCode();
}

runMetaGPT();
