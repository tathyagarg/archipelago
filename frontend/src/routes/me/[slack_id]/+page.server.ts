import type { PageServerLoad } from './$types';
import {config} from 'dotenv';
config();

const PROD = parseInt(process.env.PROD);
const USER_EP = PROD ? 'https://archipelago-api.tathya.hackclub.app/me' : 'http://localhost:8000/me';
const ISLAND_EP = PROD ? 'https://archipelago-api.tathya.hackclub.app/island' : 'http://localhost:8000/island';
const ALL_USER_EP = PROD ? 'https://archipelago-api.tathya.hackclub.app/slack' : 'http://localhost:8000/slack';

export const load: PageServerLoad = async ({ params }) => {
	const res = await fetch(`${USER_EP}?user_id=${params.slack_id}`);
	const data = await res.json();

	const img_res = await fetch(`${ISLAND_EP}?user_id=${params.slack_id}`);
	const img_data = await img_res.json();

	const all_res = await fetch(`${ALL_USER_EP}?user_id=${params.slack_id}`);
	const all_data = await all_res.json();

	return { user: data, island: img_data, all: all_data };
};
