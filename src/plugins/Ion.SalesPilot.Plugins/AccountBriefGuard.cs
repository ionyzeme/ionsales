using Microsoft.Xrm.Sdk;
using System;

namespace Ion.SalesPilot.Plugins
{
    /// <summary>
    /// Sales Intelligence Brief guard for the account table.
    ///
    /// Registered as a synchronous pre-operation step on account Create and Update.
    /// Two behaviours, both enforced server-side (so they hold no matter how the
    /// record is written — form, Web API, import):
    ///
    ///   1. Validation: an account whose <c>ion_accounthealth</c> resolves to
    ///      "At Risk" must have a non-empty <c>ion_brief</c>. This replaces the
    ///      conventional "business rule" without touching the maker portal.
    ///   2. Freshness: whenever <c>ion_brief</c> is written/changed, stamp
    ///      <c>ion_briefupdatedon</c> with the current UTC time, so the brief's
    ///      "last updated" is automatic rather than hand-entered.
    ///
    /// On Update the Target holds only changed columns, so the effective value of
    /// each field is taken from the Target if present, otherwise from a registered
    /// pre-image named "PreImage" (attributes: ion_accounthealth, ion_brief).
    /// </summary>
    public class AccountBriefGuard : PluginBase
    {
        // Local option value for "At Risk" on ion_accounthealth (see docs/schema/sales-pilot.md).
        private const int AtRisk = 100000002;

        public AccountBriefGuard(string unsecureConfiguration, string secureConfiguration)
            : base(typeof(AccountBriefGuard))
        {
        }

        protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
        {
            if (localPluginContext == null)
            {
                throw new ArgumentNullException(nameof(localPluginContext));
            }

            var context = localPluginContext.PluginExecutionContext;

            if (!context.InputParameters.Contains("Target") || !(context.InputParameters["Target"] is Entity target))
            {
                return;
            }

            if (target.LogicalName != "account")
            {
                return;
            }

            Entity preImage = context.PreEntityImages.Contains("PreImage")
                ? context.PreEntityImages["PreImage"]
                : null;

            // Freshness: if the brief is being set or changed in this write, stamp the date.
            if (target.Contains("ion_brief"))
            {
                target["ion_briefupdatedon"] = DateTime.UtcNow;
            }

            // Validation: At Risk requires a justification brief.
            var health = Effective<OptionSetValue>(target, preImage, "ion_accounthealth");
            if (health != null && health.Value == AtRisk)
            {
                var brief = Effective<string>(target, preImage, "ion_brief");
                if (string.IsNullOrWhiteSpace(brief))
                {
                    throw new InvalidPluginExecutionException(
                        "Account Health is set to \"At Risk\", so a Brief is required. " +
                        "Add a Brief explaining the risk before saving.");
                }
            }
        }

        /// <summary>
        /// Resolves the post-write value of an attribute: prefer the Target (the
        /// incoming change), fall back to the pre-image (the stored value), else default.
        /// </summary>
        private static T Effective<T>(Entity target, Entity preImage, string attribute)
        {
            if (target.Contains(attribute))
            {
                return target.GetAttributeValue<T>(attribute);
            }

            if (preImage != null && preImage.Contains(attribute))
            {
                return preImage.GetAttributeValue<T>(attribute);
            }

            return default;
        }
    }
}
