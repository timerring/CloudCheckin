let message = "";

// Cloudflare Worker
export default {
  async fetch(request, env, ctx) {
    console.log("🚀 NodeSeek Worker started - fetch handler called");
    
    const url = new URL(request.url);
    
    if (url.pathname === '/checkin') {
      return await handleNodeSeekCheckin(env);
    }
    
    // Other paths return simple information
    return new Response(
      JSON.stringify({ message: "NodeSeek Worker is running. Visit /checkin to trigger check-in." }),
      { headers: { "Content-Type": "application/json" } }
    );
  },

  async scheduled(event, env, ctx) {
    console.log("⏰ NodeSeek Scheduled handler called");
    const result = await handleNodeSeekCheckin(env);
    const resultText = await result.text();
    console.log(`📊 NodeSeek Scheduled check-in result: ${resultText}`);
  }
};

async function handleNodeSeekCheckin(env) {
  console.log("🔧 Starting NodeSeek handleCheckin");
  
  // Get cookie from environment variable
  const cookie = env.NODESEEK_COOKIE;
  
  if (!cookie) {
    console.log("❌ No NODESEEK_COOKIE found in environment");
    return new Response(
      JSON.stringify({ error: "Environment variable NODESEEK_COOKIE is not set" }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" }
      }
    );
  }
  
  console.log(`✅ cookie found, length: ${cookie.length}`);
  
  // Initialize message time (UTC+8)
  const now = new Date();
  const utc8Time = new Date(now.getTime() + 8 * 60 * 60 * 1000);
  message = utc8Time.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }) + " from NodeSeek \n";
  
  console.log(`🕐 Current time (UTC+8): ${utc8Time.toLocaleString('zh-CN')}`);
  
  console.log(`🔄 Processing single account...`);
  
  const result = await checkInAccount(cookie);
  message += `Account: ${result.message}\n`;
  
  console.log(`🎉 NodeSeek check-in completed: ${result.success ? 'successful' : 'failed'}`);
  
  return new Response(
    JSON.stringify({ 
      success: result.success, 
      message: message,
      result: result,
      summary: `Account checked in ${result.success ? 'successfully' : 'with failure'}`
    }),
    {
      headers: { "Content-Type": "application/json" }
    }
  );
}

async function checkInAccount(cookie) {
  const headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Length': '0',
    'Origin': 'https://www.nodeseek.com',
    'Referer': 'https://www.nodeseek.com/board',
    'Sec-CH-UA': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'Sec-CH-UA-Mobile': '?0',
    'Sec-CH-UA-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Cookie': cookie
  };
  
  try {
    // random=true means get random reward
    const url = 'https://www.nodeseek.com/api/attendance?random=true';
    console.log(`🌐 Account checking in at: ${url}`);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      cf: {
        // Force IPv4
        resolveOverride: 'ipv4'
      }
    });
    
    console.log(`📡 Account Status Code: ${response.status}`);
    const responseText = await response.text();
    console.log(`📄 Account Response Content: ${responseText}`);
    
    // Check if the check-in is successful
    if (response.status === 200) {
      const successMessage = `✅ Account check-in successful`;
      console.log(successMessage);
      
      // Try to parse the response content to get more information
      try {
        const responseData = JSON.parse(responseText);
        let detailMessage = successMessage;
        if (responseData.message) {
          detailMessage += ` - ${responseData.message}`;
        }
        if (responseData.data && responseData.data.reward) {
          detailMessage += ` - Reward: ${responseData.data.reward}`;
        }
        return { success: true, message: detailMessage, response: responseData };
      } catch (parseError) {
        return { success: true, message: successMessage, response: responseText };
      }
    } else {
      const failMessage = `❌ Account check-in failed, status: ${response.status}, response: ${responseText}`;
      console.log(failMessage);
      return { success: false, message: failMessage, response: responseText };
    }
    
  } catch (error) {
    const errorMessage = `💥 Account check-in process error: ${error.message}`;
    console.log(errorMessage);
    return { success: false, message: errorMessage, error: error.message };
  }
}

// Helper function: delay execution
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}