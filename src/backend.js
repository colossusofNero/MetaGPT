```javascript
// Import required modules
const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const dotenv = require('dotenv');

// Initialize dotenv to use environment variables
dotenv.config();

// Initialize the Express application
const app = express();
app.use(express.json());

// A simple in-memory "database" for demonstration purposes
const users = [];

// Middleware to validate tokens
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (token == null) return res.sendStatus(401);

    jwt.verify(token, process.env.ACCESS_TOKEN_SECRET, (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
};

// Controller: Handling user registration
const registerUser = async (req, res) => {
    try {
        const hashedPassword = await bcrypt.hash(req.body.password, 10);
        const newUser = {
            username: req.body.username,
            password: hashedPassword
        };
        users.push(newUser);
        res.status(201).json({ message: "User created" });
    } catch (err) {
        res.status(500).json({ error: "Failed to register user" });
    }
};

// Controller: Handling user login
const loginUser = async (req, res) => {
    try {
        const user = users.find(user => user.username === req.body.username);
        if (user == null) {
            return res.status(400).send('Cannot find user');
        }
        if (await bcrypt.compare(req.body.password, user.password)) {
            const userPayload = { username: user.username };
            const accessToken = jwt.sign(userPayload, process.env.ACCESS_TOKEN_SECRET);
            res.json({ accessToken: accessToken });
        } else {
            res.status(403).json({ error: "Login failed" });
        }
    } catch (err) {
        res.status(500).json({ error: "Failed to log in" });
    }
};

// Define the routes
app.post('/register', registerUser);
app.post('/login', loginUser);

// Protected route example
app.get('/protected', authenticateToken, (req, res) => {
    res.json({message: `Hello ${req.user.username}`});
});

// Set the server to listen on a port
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

```
This script sets up an Express server and includes endpoints for user registration and login, utilizing JSON Web Tokens for authentication. The `/protected` endpoint demonstrates the use of middleware for route protection based on valid JWTs. Adjustments such as tying into actual database logic and advanced error reporting are left as possible enhancements.