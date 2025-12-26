package {{ package_name }};

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView myWebView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        {% if not show_status_bar %}
        getWindow().setFlags(android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN, 
                             android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN);
        {% endif %}

        setContentView(R.layout.activity_main);

        myWebView = (WebView) findViewById(R.id.webview);
        
        {% if splash_path %}
        // Simple Splash Implementation
        final android.view.View splashView = new android.view.View(this);
        splashView.setBackgroundResource(R.drawable.splash);
        addContentView(splashView, new android.view.ViewGroup.LayoutParams(
            android.view.ViewGroup.LayoutParams.MATCH_PARENT, android.view.ViewGroup.LayoutParams.MATCH_PARENT));
        
        new android.os.Handler().postDelayed(new SplashRunnable(splashView), {{ splash_duration }});
        {% endif %}

        WebSettings webSettings = myWebView.getSettings();
        
        webSettings.setJavaScriptEnabled({{ 'true' if enable_js else 'false' }});
        webSettings.setDomStorageEnabled({{ 'true' if enable_dom else 'false' }});
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setAllowFileAccessFromFileURLs(true);
        webSettings.setAllowUniversalAccessFromFileURLs(true);
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
            webSettings.setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }
        webSettings.setMediaPlaybackRequiresUserGesture(false);
        
        {% if extras["Enable Zoom"] %}
        webSettings.setSupportZoom(true);
        webSettings.setBuiltInZoomControls(true);
        webSettings.setDisplayZoomControls(false);
        {% endif %}

        {% if user_agent %}
        webSettings.setUserAgentString("{{ user_agent }}");
        {% endif %}

        myWebView.setWebViewClient(new WebViewClient());
        
        // Prepare Headers
        java.util.Map<String, String> extraHeaders = new java.util.HashMap<>();
        {% for key, value in headers_dict.items() %}
        extraHeaders.put("{{ key }}", "{{ value }}");
        {% endfor %}

        // Load URL or Local File
        {% if web_mode == "URL (Remote)" %}
        if (extraHeaders.isEmpty()) {
            myWebView.loadUrl("{{ url }}");
        } else {
            myWebView.loadUrl("{{ url }}", extraHeaders);
        }
        {% else %}
        myWebView.loadUrl("file:///android_asset/{{ start_page }}");
        {% endif %}
    }

    @Override
    public void onBackPressed() {
        {% if extras["Exit on Back"] %}
        super.onBackPressed();
        {% else %}
        if (myWebView.canGoBack()) {
            myWebView.goBack();
        } else {
            super.onBackPressed();
        }
        {% endif %}
    }

    private static class SplashRunnable implements Runnable {
        private final android.view.View splashView;
        SplashRunnable(android.view.View view) {
            this.splashView = view;
        }
        @Override
        public void run() {
            splashView.setVisibility(android.view.View.GONE);
        }
    }
}
