```javascript
// Import necessary modules
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const dotenv = require('dotenv');

// Initialize dotenv to use variables in .env file
dotenv.config();

// Set up express app
const app = express();
app.use(express.json()); // Middleware to parse JSON bodies

// User model simulation for the sake of demonstration
let users = [];

// Function to generate JWT token
function generateToken(user) {
    return jwt.sign({ userId: user.id, username: user.username }, process.env.JWT_SECRET, { expiresIn: '1h' });
}

// Controller for user authentication
const authController = {
    async signup(req, res) {
        try {
            const { username, password } = req.body;
            const salt = await bcrypt.genSalt(10);
            const hashedPassword = await bcrypt.hash(password, salt);
            const user = { id: users.length + 1, username, password: hashedPassword };
            users.push(user);
            const token = generateToken(user);
            res.status(201).json({ message: 'User created successfully', token });
        } catch (error) {
            res.status(500).json({ message: 'Internal server error' });
        }
    },

    async login(req, res) {
        try {
            const { username, password } = req.body;
            const user = users.find(u => u.username === username);
            if (!user) return res.status(404).json({ message: 'User not found' });

            const isMatch = await bcrypt.compare(password, user.password);
            if (!isMatch) return res.status(400).json({ message: 'Invalid credentials' });

            const token = generateToken(user);
            res.status(200).json({ message: 'User logged in successfully', token });
        } catch (error) {
            res.status(500).json({ message: 'Internal server error' });
        }
    }
};

// Routes setup
const router = express.Router();

router.post('/signup', authController.signup);
router.post('/login', authController.login);

// Apply the routes to the app
app.use('/api/auth', router);

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```