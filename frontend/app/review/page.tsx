import ReviewDashboard from "@/components/ReviewDashboard";

export default function ReviewPage() {
  return (
    <>
      <h1>Rule Review</h1>
      <p className="notice">
        For leads and editors. Rules stay <strong>DRAFT</strong> until a lead explicitly changes
        the status. Nothing is ever promoted automatically, and a rule cannot be confirmed while it
        is incomplete.
      </p>
      <ReviewDashboard />
    </>
  );
}
