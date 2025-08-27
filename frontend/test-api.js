// Simple test script to verify API connection
const testAPI = async () => {
  try {
    // Test admin dashboard API
    const response = await fetch('http://localhost:8000/api/v1/adminpanel/dashboard/', {
      headers: {
        'Authorization': 'Bearer YOUR_TOKEN_HERE', // You'll need to get a valid token
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Admin Dashboard API working:', data);
    } else {
      console.log('❌ Admin Dashboard API failed:', response.status, response.statusText);
    }
  } catch (error) {
    console.log('❌ API connection failed:', error.message);
  }
};

// Test users API
const testUsersAPI = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/adminpanel/users/', {
      headers: {
        'Authorization': 'Bearer YOUR_TOKEN_HERE',
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Users API working:', data);
    } else {
      console.log('❌ Users API failed:', response.status, response.statusText);
    }
  } catch (error) {
    console.log('❌ Users API connection failed:', error.message);
  }
};

// Run tests
console.log('Testing API connections...');
testAPI();
testUsersAPI(); 