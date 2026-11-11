import { LeadOnly } from "@/components/AuthProvider";
import ReviewDashboard from "@/components/ReviewDashboard";

export default function ReviewPage() {
  return (
    <LeadOnly what="The knowledge base">
      <div className="page-wrap">
        <div className="page-kicker">Leads &amp; admins</div>
        <h1 className="page-title">Knowledge base</h1>
        <p className="page-subtitle">
          Review, complete and approve rules. Rules stay <strong>draft</strong> until a lead explicitly
          changes the status. Nothing is promoted automatically, and an incomplete rule cannot be confirmed.
        </p>
        <ReviewDashboard />
      </div>
    </LeadOnly>
  );
}
