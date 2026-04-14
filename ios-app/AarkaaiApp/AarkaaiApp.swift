import SwiftUI

@main
struct AarkaaiApp: App {
    @StateObject private var appSession = AppSession()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appSession)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var appSession: AppSession
    
    var body: some View {
        Group {
            if appSession.isCheckingAuth {
                SplashScreen()
            } else if appSession.isLoggedIn {
                ChatView(viewModel: ChatViewModel(appSession: appSession))
            } else {
                AuthView(viewModel: AuthViewModel(appSession: appSession))
            }
        }
    }
}

struct SplashScreen: View {
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        ZStack {
            (colorScheme == .dark ? AppTheme.bgDark : AppTheme.bgLight)
                .ignoresSafeArea()
            
            VStack {
                Circle()
                    .fill(AppTheme.primary)
                    .frame(width: 100, height: 100)
                    .overlay(
                        Text("A")
                            .font(.system(size: 50, weight: .bold))
                            .foregroundColor(.white)
                    )
                
                ProgressView()
                    .padding(.top, 20)
            }
        }
    }
}
