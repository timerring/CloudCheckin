// V2EX cloudcheckin
let message = "";

// Cloudflare Worker
export default {
  // Two ways to trigger the worker
  // 1. Visit /checkin
  async fetch(request, env, ctx) {
    console.log("🚀 Worker started - fetch handler called");
    
    const url = new URL(request.url);
    
    // Ignore favicon and Chrome DevTools requests
    if (url.pathname === '/favicon.ico' || 
        url.pathname.startsWith('/.well-known/') ||
        url.pathname.includes('devtools')) {
      return new Response(null, { status: 204 });
    }
    
    // Only process /checkin endpoint
    if (url.pathname === '/checkin') {
      return await handleCheckin(env);
    }
    
    // Default response for other paths
    return new Response(
      JSON.stringify({ 
        message: "V2EX Worker is running. Visit /checkin to trigger check-in.",
        endpoints: {
          checkin: "/checkin"
        }
      }),
      { 
        headers: { 
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        } 
      }
    );
  },
  // 2. Scheduled at a specific time
  async scheduled(event, env, ctx) {
    console.log("Scheduled handler called");
    const result = await handleCheckin(env);
    const resultText = await result.text();
    console.log(`Scheduled check-in result: ${resultText}`);
  }
};

async function handleCheckin(env) {
  console.log("🔧 Starting handleCheckin");
  
  // Get cookie from environment variable
  const cookie = env.V2EX_COOKIE;
  
  if (!cookie) {
    console.log("No V2EX_COOKIE found in environment");
    return new Response(
      JSON.stringify({ error: "Environment variable V2EX_COOKIE is not set" }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" }
      }
    );
  }
  
  console.log(`Cookie found, length: ${cookie.length}`);
  
  // Initialize message time (UTC+8)
  const now = new Date();
  const utc8Time = new Date(now.getTime());
  message = utc8Time.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '/') + " from V2EX \n";
  
  console.log(`Current time (UTC+8): ${utc8Time.toLocaleString('zh-CN')}`);

  const headers = {
    "Referer": "https://www.v2ex.com/mission/daily",
    "Host": "www.v2ex.com",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; Redmi K30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.83 Mobile Safari/537.36",
    "Cookie": cookie
  };
  
  try {
    console.log("Getting once number and sign status...");
    // Get once number and sign status
    const { once, signed } = await getOnce(headers);
    console.log(`Signed: ${signed}`);
    // Check sign in
    if (once && !signed) {
      // const success = await checkIn(once, headers);
      // if (!success) {
      //   console.log("Check in failed");
      //   throw new Error("Fail to check in");
      // }
    
      const { time: timeStr, balance: balanceStr } = await getBalance(headers);
      if (!timeStr || !balanceStr) {
        console.log("Failed to get balance");
        throw new Error("Fail to get balance");
      }
      
      message += `Balance check time: ${timeStr}, Balance: ${balanceStr}\n`;
      // console.log(`Your balance: ${balanceStr} at ${timeStr}`);
    } else if (signed) {
      console.log("Already signed today, checking balance...");
      message += "Already signed today, checking balance...\n";
      const { time: timeStr, balance: balanceStr } = await getBalance(headers);
      if (timeStr && balanceStr) {
        message += `Balance check time: ${timeStr}, Balance: ${balanceStr}\n`;
        console.log(`💰 Current balance: ${balanceStr} at ${timeStr}`);
      }
    } else {
      console.log("Failed to get once number");
      message += "FAIL.\n";
      throw new Error("Fail to check in");
    }
    return new Response(
      JSON.stringify({ success: true, message: message }),
      {
        headers: { "Content-Type": "application/json" }
      }
    );
  } catch (err) {
    console.log(`Error occurred: ${err.message}`);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: err.message, 
        message: message 
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" }
      }
    );
  }
}

async function getOnce(headers) {
  const url = "https://www.v2ex.com/mission/daily";
  console.log(`Fetching: ${url}`);
  
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: headers,
      cf: {
        // Force IPv4
        resolveOverride: 'ipv4'
      }
    });
    
    const content = await response.text();
    // console.log(`Response: ${content}`);
    
    // Check if need to login
    if (content.includes("需要先登录")) {
      console.log("Cookie is outdated - need to login");
      message += "The cookie is outdated. Please update the cookie.";
      return { once: null, signed: false };
    }
    
    // Check if already signed
    if (content.includes("每日登录奖励已领取")) {
      console.log("Already signed today");
      message += "You have already signed today.\n";
      return { once: null, signed: true };
    }
    
    // Extract once number
    const onceMatch = content.match(/redeem\?once=([^']+)'/);
    if (onceMatch) {
      const once = onceMatch[1];
      console.log(`Successfully got once: ${once}`);
      message += `Successfully get once ${once}\n`;
      return { once: once, signed: false };
    } else {
      console.log("Failed to get once number from page");
      message += "Have not signed, but fail to get once\n";
      return { once: null, signed: false };
    }
    
  } catch (error) {
    console.log(`Error in getOnce: ${error.message}`);
    message += `Error in getOnce: ${error.message}\n`;
    return { once: null, signed: false };
  }
}

async function checkIn(once, headers) {
  const url = `https://www.v2ex.com/mission/daily/redeem?once=${once}`;
  console.log(`Check-in URL: ${url}`);
  
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: headers,
      cf: {
        // Force IPv4
        resolveOverride: 'ipv4'
      }
    });
    
    const content = await response.text();
    // console.log(`Check-in response: ${content}`);
    if (content.includes("已成功领取每日登录奖励")) {
      console.log("Check in successful!");
      message += "Check in successfully\n";
      return true;
    } else {
      console.log("Check in failed - success message not found");
      message += "Fail to check in\n";
      return false;
    }

  } catch (error) {
    console.log(`Error in checkIn: ${error.message}`);
    message += `Error in checkIn: ${error.message}\n`;
    return false;
  }
}

async function getBalance(headers) {
  const url = "https://www.v2ex.com/balance";
  console.log(`Fetching balance: ${url}`);
  
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: headers,
      cf: {
        // Force IPv4
        resolveOverride: 'ipv4'
      }
    });
    
    const content = await response.text();
    
    // Using the regex to extract the balance info
    const pattern = /每日登录奖励.*?<small class="gray">(.*?)<\/small>.*?<td class="d" style="text-align: right;">.*?<\/td>.*?<td class="d" style="text-align: right;">(.*?)<\/td>/s;
    const match = content.match(pattern);
    
    if (match) {
      const time = match[1].trim();
      const balance = match[2].trim();
      console.log(`Balance info found - Time: ${time}, Balance: ${balance}`);
      message += "Successfully got balance info\n";
      return { time: time, balance: balance };
    } else {
      console.log("Failed to parse balance info from page");
      message += "Failed to get balance info\n";
      return { time: null, balance: null };
    }

  } catch (error) {
    console.log(`Error in getBalance: ${error.message}`);
    message += `Error in getBalance: ${error.message}\n`;
    return { time: null, balance: null };
  }
} 