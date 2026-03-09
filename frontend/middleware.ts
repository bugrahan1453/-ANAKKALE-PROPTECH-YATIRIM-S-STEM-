import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value;
  const { pathname } = request.nextUrl;

  // Login sayfası hariç, token yoksa login'e yönlendir
  if (!pathname.startsWith("/login") && !pathname.startsWith("/_next") && !pathname.startsWith("/api")) {
    // Client-side localStorage kontrolü middleware'de yapılamaz
    // Bu yönlendirme frontend tarafında api.ts interceptor'da yapılıyor
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
