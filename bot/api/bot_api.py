from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import requests
from utils.dotenv_config import WEATHER_API_KEY

# Initialize router
router = Router()

# In-memory storage for user data
users_storage = {}

# Define states for user profile setup
class Profile(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()


def setup_handlers(dp):
    """Register the router with the dispatcher."""
    dp.include_router(router)

@router.message(Command("start"))
async def start_command(message: Message):
    """Display a welcome message and list of available commands."""
    welcome_message = (
        "🌟 Welcome to the Health Tracker Bot! 🌟\n\n"
        "Here are the commands you can use:\n\n"
        "1. /set_profile - Set up your profile (weight, height, age, activity, city).\n"
        "   Usage: /set_profile\n\n"
        "2. /log_water - Log your daily water intake.\n"
        "   Usage: /log_water <amount in ml>\n\n"
        "3. /log_food - Log the food you ate and calculate calories.\n"
        "   Usage: /log_food <food name>\n\n"
        "4. /log_workout - Log your workout and track burned calories.\n"
        "   Usage: /log_workout <workout type> <duration in minutes>\n\n"
        "5. /check_progress - Check your daily progress (water and calories).\n"
        "   Usage: /check_progress\n\n"
        "Start by setting up your profile using /set_profile!"
    )
    await message.reply(welcome_message)
    
@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    """Start the profile setup process by asking for weight."""
    await message.reply("Please enter your weight (in kg):")
    await state.set_state(Profile.weight)


@router.message(Profile.weight)
async def process_weight(message: Message, state: FSMContext):
    """Process user's weight input and ask for height."""
    try:
        weight = int(message.text)
        await state.update_data(weight=weight)
        await message.reply("Please enter your height (in cm):")
        await state.set_state(Profile.height)
    except ValueError:
        await message.reply("Please enter a valid number.")


@router.message(Profile.height)
async def process_height(message: Message, state: FSMContext):
    """Process user's height input and ask for age."""
    try:
        height = int(message.text)
        await state.update_data(height=height)
        await message.reply("Please enter your age:")
        await state.set_state(Profile.age)
    except ValueError:
        await message.reply("Please enter a valid number.")


@router.message(Profile.age)
async def process_age(message: Message, state: FSMContext):
    """Process user's age input and ask for daily activity."""
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.reply("How many minutes of activity do you have per day?")
        await state.set_state(Profile.activity)
    except ValueError:
        await message.reply("Please enter a valid number.")


@router.message(Profile.activity)
async def process_activity(message: Message, state: FSMContext):
    """Process user's activity input and ask for city."""
    try:
        activity = int(message.text)
        await state.update_data(activity=activity)
        await message.reply("Which city are you located in?")
        await state.set_state(Profile.city)
    except ValueError:
        await message.reply("Please enter a valid number.")


@router.message(Profile.city)
async def process_city(message: Message, state: FSMContext):
    """Process user's city input, calculate goals, and save profile."""
    city = message.text
    await state.update_data(city=city)
    data = await state.get_data()

    # Calculate water and calorie goals
    weight = data['weight']
    activity = data['activity']
    water_goal = int(weight * 30 + 500 * (activity // 30))

    # Fetch temperature data for the city
    response = requests.get(
        f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )
    if response.status_code == 200:
        temperature = response.json()['main']['temp']
        if temperature > 25:
            water_goal += 500

    calorie_goal = int(10 * weight + 6.25 * data['height'] - 5 * data['age'])
    if activity > 50:
        calorie_goal += 300

    # Save user profile
    user_id = message.from_user.id
    users_storage[user_id] = {
        'weight': weight,
        'height': data['height'],
        'age': data['age'],
        'activity': activity,
        'city': city,
        'water_goal': water_goal,
        'calorie_goal': calorie_goal,
        'logged_water': 0,
        'logged_calories': 0,
        'burned_calories': 0,
    }

    await state.clear()
    await message.reply(
        f"Profile setup complete!\n"
        f"Daily goals:\n"
        f"💧 Water: {water_goal} ml\n"
        f"🔥 Calories: {calorie_goal} kcal."
    )


@router.message(Command("log_water"))
async def log_water(message: Message):
    """Log water consumption for the user."""
    try:
        user_id = message.from_user.id

        if user_id not in users_storage:
            await message.reply("You cannot log data because your profile is not set up.")
            return

        raw_data = message.text.split()

        if len(raw_data) < 2:
            await message.reply("You did not specify how much water you drank.")
            return

        water_consumed = int(raw_data[1])
        users_storage[user_id]["logged_water"] += water_consumed
        remaining_water = users_storage[user_id]["water_goal"] - users_storage[user_id]["logged_water"]

        await message.reply(f"You have {max(0, remaining_water)} ml of water left to drink today.")

    except ValueError:
        await message.reply("Please enter a valid number.")


async def process_eaten_food(message: Message, user_id: int, calories_per_100g: int):
    """Process the amount of food eaten and log calories."""
    try:
        quantity = int(message.text)
        total_calories = int((quantity / 100) * calories_per_100g)
        users_storage[user_id]['logged_calories'] += total_calories
        await message.reply(f"Logged: {total_calories} kcal.")
    except ValueError:
        await message.reply("Please enter the weight in grams.")


@router.message(Command("log_food"))
async def log_food(message: Message):
    """Log food consumption for the user."""
    try:
        user_id = message.from_user.id

        if user_id not in users_storage:
            await message.reply("You cannot log data because your profile is not set up.")
            return

        raw_data = message.text.split()

        if len(raw_data) < 2:
            await message.reply("You did not specify what you ate.")
            return

        food_name = raw_data[1]
        url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={food_name}&json=true"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            if products:
                first_product = products[0]
                calories_per_100g = first_product.get('nutriments', {}).get('energy-kcal_100g', 0)

                if calories_per_100g is None:
                    await message.reply("Something went wrong. Please try again.")
                    return

                await message.reply(f"{food_name} — {calories_per_100g} kcal per 100g. How many grams did you eat?")

                @router.message()
                async def handle_eaten_food(message: Message):
                    await process_eaten_food(message, user_id, calories_per_100g)

            return None
        print(f"Error: {response.status_code}")
        return None
    except ValueError:
        await message.reply("Something went wrong. Please try again.")


@router.message(Command("log_workout"))
async def log_workout(message: Message):
    """Log workout details and calculate burned calories."""
    try:
        user_id = message.from_user.id

        if user_id not in users_storage:
            await message.reply("You cannot log data because your profile is not set up.")
            return

        raw_data = message.text.split()

        if len(raw_data) < 3:
            await message.reply(
                "Incomplete workout details.\nUse: /log_workout <workout type> <duration (minutes)>"
            )
            return

        workout_type = raw_data[1]
        workout_duration = int(raw_data[2])

        # Calculate burned calories and additional water intake
        burned_calories = workout_duration * 10
        additional_water = int((workout_duration / 30) * 200)

        users_storage[user_id]["burned_calories"] += burned_calories
        users_storage[user_id]["logged_water"] += additional_water

        await message.reply(
            f"🏃‍️ {workout_type} for {workout_duration} minutes — {burned_calories} kcal burned. "
            f"Additional recommendation: drink {additional_water} ml of water."
        )

    except ValueError:
        await message.reply("Invalid input. Please try again.")


@router.message(Command("check_progress"))
async def check_progress(message: Message):
    """Check and display user's progress."""
    try:
        user_id = message.from_user.id

        if user_id not in users_storage:
            await message.reply("You cannot check progress because your profile is not set up.")
            return

        user = users_storage[user_id]

        reply = (
            f"📊 Your progress:\n"
            f"- Water consumed: {user['logged_water']} ml out of {user['water_goal']} ml.\n"
            f"- Remaining water: {max(0, user['water_goal'] - user['logged_water'])} ml.\n\n"
            f"Calories:\n"
            f"- Consumed: {user['logged_calories']} kcal out of {user['calorie_goal']} kcal.\n"
            f"- Burned: {user['burned_calories']} kcal.\n"
            f"- Net balance: {max(0, user['logged_calories'] - user['burned_calories'])} kcal."
        )

        await message.reply(reply)

    except ValueError:
        await message.reply("Invalid input. Please try again.")