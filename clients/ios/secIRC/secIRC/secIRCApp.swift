import SwiftUI

@main
struct secIRCApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var isLoggedIn = false
    
    var body: some View {
        if isLoggedIn {
            MainView()
        } else {
            LoginView(onLoginSuccess: {
                isLoggedIn = true
            })
        }
    }
}

#Preview {
    ContentView()
}
