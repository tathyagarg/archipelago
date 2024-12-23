import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	const res = await fetch(`https://archipelago-api.tathya.hackclub.app/me?user_id=${params.slack_id}`);
	const data = await res.json();

	return { data };
};
