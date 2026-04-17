/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { discussSidebarItemsRegistry } from "@mail/core/public_web/discuss_sidebar";
import { useService } from "@web/core/utils/hooks";

export class TawkDiscussSidebar extends Component {
    static template = "tawk_discuss_integration.TawkDiscussSidebar";
    static props = {};

    setup() {
        this.store = useState(useService("mail.store"));
        this.orm = useService("orm");
        this.state = useState({
            open: true,
            threads: [],
            loaded: false,
        });

        onWillStart(async () => {
            await this.loadThreads();
        });
    }

    async loadThreads() {
        try {
            const result = await this.orm.call(
                "tawk.discuss.thread",
                "get_sidebar_threads",
                [],
                {}
            );
            console.log("✅ Tawk sidebar threads:", result);
            this.state.threads = Array.isArray(result) ? result : [];
        } catch (error) {
            console.error("❌ Failed to load Tawk threads", error);
            this.state.threads = [];
        } finally {
            this.state.loaded = true;
        }
    }

    toggleSection() {
        this.state.open = !this.state.open;
    }

    async openThread(threadData) {
        console.log("==== CLICK DEBUG ====");
        console.log("Thread Data:", threadData);

        if (!threadData || !threadData.channel_id) {
            console.error("❌ Invalid thread data");
            return;
        }

        try {
            const thread = await this.store.Thread.getOrFetch({
                model: "discuss.channel",
                id: threadData.channel_id,
            });

            console.log("✅ Fetched Thread:", thread);
            console.log("✅ Fetched Thread ID:", thread?.id);
            console.log("✅ Fetched Thread Name:", thread?.name);

            if (!thread) {
                console.error("❌ Thread not fetched from store");
                return;
            }

            thread.setAsDiscussThread();
        } catch (error) {
            console.error("❌ ERROR while opening thread:", error);
        }
    }
}

discussSidebarItemsRegistry.add("tawk_discuss_sidebar", TawkDiscussSidebar, {
    sequence: 25,
});