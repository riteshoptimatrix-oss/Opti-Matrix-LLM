import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);
    
    if (!body || !body.question || typeof body.question !== "string" || !body.question.trim()) {
      return NextResponse.json(
        {
          success: false,
          answer: "Please provide a valid question.",
          error: "Empty or invalid question"
        },
        { status: 400 }
      );
    }

    const question = body.question.trim();
    const mlApiUrl = process.env.ML_API_URL || "http://127.0.0.1:8000";

    try {
      const mlResponse = await fetch(`${mlApiUrl}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!mlResponse.ok) {
        console.error(`ML API responded with status: ${mlResponse.status}`);
        return NextResponse.json({
          success: false,
          answer: "I'm sorry, I encountered an issue retrieving an answer. Please contact Opti Matrix for more information.",
          error: `Backend status ${mlResponse.status}`
        });
      }

      const mlData = await mlResponse.json();

      return NextResponse.json({
        success: mlData.success ?? true,
        intent: mlData.intent ?? null,
        answer: mlData.answer ?? "I'm sorry, I don't have enough information to answer that question accurately. Please contact Opti Matrix for more information.",
        confidence: mlData.confidence ?? 0,
        matched: mlData.matched ?? false
      });
    } catch (networkErr: any) {
      console.error("Error communicating with Python FastAPI ML service:", networkErr);
      return NextResponse.json({
        success: false,
        answer: "I am having trouble connecting to the knowledge service. Please ensure the Python FastAPI backend is running on port 8000.",
        error: "ML service offline"
      });
    }
  } catch (err: any) {
    console.error("Next.js /api/chat route error:", err);
    return NextResponse.json(
      {
        success: false,
        answer: "An unexpected error occurred. Please try again.",
        error: "Internal Server Error"
      },
      { status: 500 }
    );
  }
}
