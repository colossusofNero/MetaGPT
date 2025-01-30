```javascript
// server.js

const express = require('express');
const dotenv = require('dotenv');
const userRoutes = require('./routes/userRoutes');

dotenv.config();

const app = express();

app.use(express.json());

// Routing setup
app.use('/api/users', userRoutes);

// Generic error handler
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send({
        success: false,
        message: 'Internal server error'
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
```

```javascript
// routes/userRoutes.js

const express = require('express');
const { register, login } = require('../controllers/userController');

const router = express.Router();

// Registration route
router.post('/register', register);

// Login route
router.post('/login', login);

module.exports = router;
```

```javascript
// controllers/userController.js

const userService = require('../services/userService');

exports.register = async (req, res) => {
    try {
        const user = await userService.registerUser(req.body);
        res.status(201).send({
            success: true,
            data: user,
            message: 'User registered successfully'
        });
    } catch (error) {
        res.status(500).send({
            success: false,
            message: error.message
        });
    }
};

exports.login = async (req, res) => {
    try {
        const token = await userService.authenticateUser(req.body);
        res.status(200).send({
            success: true,
            token: token
        });
    } catch (error) {
        res.status(401).send({
            success: false,
            message: error.message
        });
    }
};
```

```javascript
// services/userService.js

const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const users = []; // This would typically be a database

exports.registerUser = async ({ username, password }) => {
    if (users.find(user => user.username === username)) {
        throw new Error('User already exists');
    }

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const newUser = {
        id: users.length + 1,
        username,
        password: hashedPassword
    };

    users.push(newUser);
    return { id: newUser.id, username: newUser.username };
};

exports.authenticateUser = async ({ username, password }) => {
    const user = users.find(user => user.username === username);
    if (!user) {
        throw new Error('User not found');
    }

    const passwordMatch = await bcrypt.compare(password, user.password);
    if (!passwordMatch) {
        throw new Error('Password incorrect');
    }

    const token = jwt.sign(
        { id: user.id, username: user.username },
        process.env.JWT_SECRET,
        { expiresIn: '1h' }
    );

    return token;
};
```

```javascript
// .env - example environment file

PORT=3000
JWT_SECRET=your_jwt_secret
```