import RuleList from "@/components/RuleList";

export default function RulesPage() {
  return (
    <>
      <h1>Rules</h1>
      <p className="notice">
        These are <strong>draft internal team guidance</strong> rules. They have{" "}
        <strong>not yet been confirmed</strong> against the official style manual and must not
        be treated as official style-manual rules.
      </p>
      <RuleList />
    </>
  );
}
