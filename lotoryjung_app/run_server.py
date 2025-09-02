#!/usr/bin/env python3
"""
Simple Flask server runner without SocketIO
"""
from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Starting Lotoryjung Flask Server...")
    print("📱 Access the application at: http://127.0.0.1:8080")
    print("🔧 Admin login: admin / admin123")
    print("👤 Test user login: testuser / test123")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(
            host='0.0.0.0', 
            port=8080, 
            debug=True,
            use_reloader=False,  # Disable reloader to avoid issues
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
