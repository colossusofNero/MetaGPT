Here is a React component for a login form with email, password, and submit button:

```jsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';

export default function LoginForm() {
  const { register, handleSubmit, errors } = useForm();
  const [submitting, setSubmitting] = useState(false);

  function onSubmit(data) {
    setSubmitting(true);
    // submit logic here
    setSubmitting(false); 
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="email">Email</label> 
        <input
          ref={register({
            required: 'Email is required',
            pattern: {
              value: /^[^@ ]+@[^@ ]+\.[^@ .]{2,}$/,
              message: 'Email is not formatted properly' 
            }
          })}
          id="email"
          name="email"
          type="email"
          aria-invalid={errors.email ? 'true' : 'false'}
        />
        {errors.email && <p role="alert">{errors.email.message}</p>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          ref={register({ 
            required: 'Password is required',
            minLength: {
              value: 8,
              message: 'Password must be at least 8 characters'
            }  
          })}
          id="password"
          name="password" 
          type="password"
          aria-invalid={errors.password ? 'true' : 'false'} 
        />
        {errors.password && <p role="alert">{errors.password.message}</p>}
      </div>

      <button type="submit" disabled={submitting}>
        {submitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  );
}
```

This implements email and password validation with React Hook Form, appropriate ARIA attributes for accessibility, and state for submission. It is a reusable component exported for use in other files.