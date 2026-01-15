import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Edge-compatible Base64 decode function
function base64Decode(str: string): string {
    try {
        // Use TextDecoder for Edge Runtime compatibility
        const bytes = Uint8Array.from(atob(str), c => c.charCodeAt(0))
        return new TextDecoder().decode(bytes)
    } catch {
        // If atob fails, try with Buffer (Node.js fallback)
        try {
            return Buffer.from(str, 'base64').toString('utf-8')
        } catch {
            return ''
        }
    }
}

export function middleware(req: NextRequest) {
    // If running in development (localhost), skip auth
    // if (process.env.NODE_ENV === 'development') {
    //   return NextResponse.next()
    // }

    const authHeader = req.headers.get('authorization')

    if (authHeader) {
        const [authType, authValue] = authHeader.split(' ')

        // Handle Bearer tokens (Cloud Run IAM) - allow through
        if (authType === 'Bearer' && authValue) {
            // Bearer tokens from Cloud Run IAM are already validated by the platform
            return NextResponse.next()
        }

        // Handle Basic auth
        if (authType === 'Basic' && authValue) {
            try {
                const decoded = base64Decode(authValue)
                const [user, pwd] = decoded.split(':')

                // HARDCODED SOVEREIGN CREDENTIALS (v1)
                // Ideally, these come from ENV vars: HUD_USER / HUD_PASS
                // But for the "Unified Container", we can default to 'admin' / 'nucleus'
                // or read from process.env
                const validUser = process.env.HUD_USER || 'admin'
                const validPass = process.env.HUD_PASS || 'nucleus'

                if (user === validUser && pwd === validPass) {
                    return NextResponse.next()
                }
            } catch {
                // Invalid Base64, fall through to 401
            }
        }
    }

    return new NextResponse('Auth Required', {
        status: 401,
        headers: {
            'WWW-Authenticate': 'Basic realm="Secure Area"',
        },
    })
}

export const config = {
    matcher: '/:path*',
}
