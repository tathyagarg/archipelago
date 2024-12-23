import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	const res = await fetch(`https://archipelago-api.tathya.hackclub.app/me?user_id=${params.slack_id}`);
	const data = await res.json();

	const img_res = await fetch(`https://archipelago-api.tathya.hackclub.app/island?user_id=${params.slack_id}`);
	const img_data = await img_res.json();

	return { user: data, island: img_data };
};
