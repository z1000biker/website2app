import SwiftUI
import WebKit

struct ContentView: View {
    var body: some View {
        WebView(url: {% if web_mode == "URL (Remote)" %}URL(string: "{{ url }}")!{% else %}Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "www")!{% endif %})
            .edgesIgnoringSafeArea(.all)
    }
}

struct WebView: UIViewRepresentable {
    let url: URL
    
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        
        {% if enable_file_access %}
        config.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
        {% endif %}
        
        let webView = WKWebView(frame: .zero, configuration: config)
        
        {% if user_agent %}
        webView.customUserAgent = "{{ user_agent }}"
        {% endif %}
        
        return webView
    }
    
    func updateUIView(_ uiView: WKWebView, context: Context) {
        let request = NSMutableURLRequest(url: url)
        
        {% for key, value in headers_dict.items() %}
        request.addValue("{{ value }}", forHTTPHeaderField: "{{ key }}")
        {% endfor %}
        
        {% if web_mode == "URL (Remote)" %}
        uiView.load(request as URLRequest)
        {% else %}
        uiView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        {% endif %}
    }
}
