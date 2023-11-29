# rosella
A simple AWS and Python approach to web development.

AWS is heavily focussed on web scale applications but there are a number of features that support small, simple and inexpensive web based applications.

## Objectives
1. Low cognitive load — The time to context switch to an existing application should be very low so that a small change can be created, tested and deployed in ten to thirty minutes. Very few code abstractions are used.
2. Inexpensive — It should be possible to create and deploy an application using low-cost pay-as-you-go AWS services.
3. Ease of Use — An application should be easy to use with no training.
4. A set of components can can be reused or copied — There is no attempt to create standard customisable code (apart from a simply utility Python package) as the congnitative load is too high as options are added for each use case. The preference is just to copy and adapt code.

The outcome is that:
1. All applications can be easily understood and quickly updated and maintained.
2. Refactoring over time is a good thing and a relatively straightforward process.
3. Each application can copy existing code or create smething new, for example for HTML generation. A loose toolkit.

## Design
The plan is to create one simple way to do things.

#### Key design elements
1. A collection/item data model is defined using AWS DynamoDB (where the collection name is the partion key and the item ID is the sort key).
2. Each portal is a single API gateway with a custom URL (e.g. portal.example.com) and an AWS Lambda function for eachmodule in the application.
3. A Lambda function is included as an "authorizer" for all proected resource. It authenticates each page and API call.
4. Role based — Each user is assigned on or more roles and an organisation which are used to authorise access to resources.
5. Simple email based authentication with no passwords — The user enters an email address and receives an email containing a magic link to sign-in.
6. All HTML uses files (with variable substitution) or is generated on-the-fly mixing in data as needed.
7. BootStrap 5.3 is used for CSS and Bootstrap Table (most commonly using JSON API calls).
8. When the user signs-in they are presented with portal items related to their role.

#### Code is organised in three levels
1. HTML, using a common template, is created in one or more Lambda functions that are responsible for authorising what pages are available to each user and role.
2. JSON client API's are defined using on or more data focussed Lambda functions whcih also authorise what data is available for each user and role.
3. An EC2 based, token protected, data server is available for Lambda function to use. It contains no user or role authorisation and is not available to clients. As well as some standard API functions, additional function can be created as needed to standardise data structures and reduce the result size which improves performance.

#### Notes
1. Portal based UI
2. DynamoDB (with _collection and _item)
5. One API Gateway for the portal and one for test-portal
6. A Lambda function for each module
7. Lambda function auth as an authorizer for authentication
8. S3 for asset and file storage (no public access to the bucket — everything through an S3 function) which limits maximum file size.
9. Javascript library TBD (custom, a library)

## Implementation
1. Examples will use the AWS Melbourne region by default.
2. The data server will work with EC2 an t4g.micro instance. It will also work with a t4g.nano instance for small applications.

#### Notes
1. Portal items are preferred over a complex menu system as it more clearly identifes the actions available to a user.
