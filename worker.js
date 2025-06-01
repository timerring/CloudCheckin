export default {
    async scheduled(event, env, ctx) {
      try {
        const WEBHOOK_URL = env.CIRCLECI_WEBHOOK_URL;
        const response = await fetch(WEBHOOK_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] Scheduled request executed`);
        console.log(`Response status: ${response.status}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`HTTP error! status: ${response.status}, body: ${errorText}`);
        } else {
          const result = await response.text();
          console.log('Response body:', result);
        }
        
      } catch (error) {
        console.error('Scheduled request failed:', error);
      }
    },
  
    // async fetch(request, env, ctx) {
    //   // Test endpoint
    //   if (request.url.includes('/test')) {
    //     try {
    //       const WEBHOOK_URL = env.CIRCLECI_WEBHOOK_URL;
    //       const response = await fetch(WEBHOOK_URL, {
    //         method: 'POST',
    //         headers: {
    //           'Content-Type': 'application/json',
    //         },
    //       });
          
    //       const responseText = await response.text();
          
    //       return new Response(`Test request completed. Status: ${response.status}\nResponse: ${responseText}`, {
    //         status: 200,
    //         headers: { 'Content-Type': 'text/plain' }
    //       });
    //     } catch (error) {
    //       return new Response(`Test failed: ${error.message}`, { 
    //         status: 500,
    //         headers: { 'Content-Type': 'text/plain' }
    //       });
    //     }
    //   }
      
    //   return new Response('CircleCI Scheduler Worker is running', { 
    //     status: 200,
    //     headers: { 'Content-Type': 'text/plain' }
    //   });
    // }
  };