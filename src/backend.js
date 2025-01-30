```javascript
// Import necessary modules
const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
require('dotenv').config();

// Create a new Express application
const app = express();

// Middleware to parse JSON bodies
app.use(express.json());

// Mock Users Database
const users = [];

// Service Layer: for handling business logic
class AuthService {
    async hashPassword(password) {
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);
        return hashedPassword;
    }

    async validatePassword(plainPassword, hashedPassword) {
        return bcrypt.compare(plainPassword, hashedPassword);
    }

    generateToken(user) {
        return jwt.sign({ id: user.id, email: user.email },
            process.env.JWT_SECRET,
            { expiresIn: '1h' }
        );
    }
}

// Controller Layer
class AuthController {
    constructor(authService) {
        this.authService = authService;
    }

    async register(req, res) {
        try {
            const { email, password } = req.body;
            if(users.some(user => user.email === email)) {
                return res.status(409).json({ message: 'Email already exists' });
            }

            const hashedPassword = await this.authService.hashPassword(password);
            const newUser = { id: users.length + 1, email, password: hashedPassword };
            users.push(newUser);

            res.status(201).json({ message: 'User created successfully', userId: newUser.id });
        } catch (error) {
            res.status(500).json({ message: 'Server error' });
        }
    }

    async login(req, res) {
        try {
            const { email, password } = req.body;
            const user = users.find(u => u.email === email);

            if (!user) {
                return res.status(401).json({ message: 'Invalid credentials' });
            }

            const validPassword = await this.authService.validatePassword(password, user.password);
            if (!validPassword) {
                return res.status(401).json({ message: 'Invalid credentials' });
            }

            const token = this.authService.generateToken(user);

            res.json({ message: 'Logged in successfully', token });
        } catch (error) {
            res.status(500).json({ message: 'Server error' });
        }
    }
}

// Routes Layer
function authRoutes(app, controller) {
    app.post('/register', (req, res) => controller.register(req, res));
    app.post('/login', (req, res) => controller.login(req, res));
}

// Initialize service and controller
const authService = new AuthService();
const authController = new AuthController(authService);

// Setup routes
authRoutes(app, authController);

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
```
This Node.js script sets up an Express server for user registration and login using JWT for authentication and bcrypt for password hashing. It demonstrates how to structure an Express app using services for business logic, controllers for handling requests, and a simple route setup, with environment variables and basic error handling.