// Debug script to check authentication status
console.log('=== Authentication Debug ===');

// Check if tokens exist
const accessToken = localStorage.getItem('access_token');
const refreshToken = localStorage.getItem('refresh_token');

console.log('Access Token:', accessToken ? '✅ Exists' : '❌ Missing');
console.log('Refresh Token:', refreshToken ? '✅ Exists' : '❌ Missing');

if (accessToken) {
  console.log('Access Token (first 20 chars):', accessToken.substring(0, 20) + '...');
}

// Test API call with token
const testAPIWithAuth = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/adminpanel/users/', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    console.log('API Response Status:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ API call successful:', data);
    } else {
      const errorData = await response.json();
      console.log('❌ API call failed:', errorData);
    }
  } catch (error) {
    console.log('❌ API call error:', error.message);
  }
};

if (accessToken) {
  testAPIWithAuth();
} else {
  console.log('❌ No access token available for testing');
} 